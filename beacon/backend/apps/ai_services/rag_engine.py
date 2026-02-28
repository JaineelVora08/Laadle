from google import genai
from django.conf import settings
from apps.ai_services.embedding_generator import EmbeddingGenerator


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Retrieves similar past Q&A pairs from Pinecone, feeds to Gemini for provisional answer.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.embedding_gen = EmbeddingGenerator()

    def retrieve_similar_cases(self, query_embedding: list, domain_id: str) -> list:
        """
        Queries Pinecone filtered by domain_id.
        Retrieves both main queries and resolved follow-ups.
        Returns: list of { query_text, advice_text, trust_score, senior_id, similarity_score, type }
        """
        results = self.embedding_gen.query_similar(
            embedding=query_embedding,
            top_k=5,
            filter={"domain_id": str(domain_id)}
        )
        return [
            {
                'query_text': r['metadata'].get('query_text', ''),
                'advice_text': r['metadata'].get('advice_text', r['metadata'].get('answer_text', '')),
                'trust_score': r['metadata'].get('trust_score', 0.0),
                'senior_id': r['metadata'].get('senior_id', ''),
                'similarity_score': r['score'],
                'type': r['metadata'].get('type', 'query')
            }
            for r in results
            if r['metadata'].get('advice_text') or r['metadata'].get('answer_text')
        ]

    def retrieve_similar_followups(self, query_embedding: list, domain_id: str, top_k: int = 3) -> list:
        """
        Queries Pinecone filtered by type='resolved_followup' and domain_id.
        Returns: list of { question_text, answer_text, similarity_score, parent_query_id }
        """
        results = self.embedding_gen.query_similar(
            embedding=query_embedding,
            top_k=top_k,
            filter={
                "domain_id": str(domain_id),
                "type": "resolved_followup",
            }
        )
        return [
            {
                'question_text': r['metadata'].get('question_text', ''),
                'answer_text': r['metadata'].get('answer_text', ''),
                'similarity_score': r['score'],
                'parent_query_id': r['metadata'].get('parent_query_id', ''),
            }
            for r in results
            if r['metadata'].get('answer_text')
        ]

    def generate_provisional_response(self, student_query: str, similar_cases: list,
                                       high_trust_advice: list) -> str:
        """
        Builds prompt from retrieved context + high-trust advice.
        Calls Gemini API.
        Returns: provisional answer string (includes disclaimer)
        """
        context_parts = []
        for i, case in enumerate(similar_cases[:3], 1):
            context_parts.append(
                f"Past Case {i} (trust: {case['trust_score']:.2f}):\n"
                f"  Q: {case['query_text']}\n"
                f"  A: {case['advice_text']}"
            )

        advice_parts = []
        for i, advice in enumerate(high_trust_advice[:3], 1):
            advice_parts.append(
                f"Senior Advice {i} (trust: {advice['trust_score']:.2f}): {advice['advice_text']}"
            )

        context_text = "\n\n".join(context_parts) if context_parts else "No similar past cases found."
        advice_text = "\n".join(advice_parts) if advice_parts else "No high-trust advice available yet."

        prompt = f"""You are BEACON, an AI mentoring assistant. A student has asked a question.
Based on similar past questions and trusted senior advice, provide a helpful provisional answer.

STUDENT QUESTION:
{student_query}

SIMILAR PAST CASES:
{context_text}

HIGH-TRUST SENIOR ADVICE:
{advice_text}

Provide a clear, helpful answer. End with a disclaimer that this is a provisional AI-generated response
and a verified senior mentor will review and provide personalized guidance soon."""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"[RAGEngine] Gemini API error: {e}")
            return (
                "[Provisional answer unavailable — AI service is temporarily rate-limited. "
                "A senior mentor will provide guidance shortly.]"
            )


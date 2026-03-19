from google import genai
from django.conf import settings
from apps.ai_services.embedding_generator import EmbeddingGenerator

import logging
logger = logging.getLogger(__name__)


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

    def retrieve_past_senior_responses(self, query_text: str, domain_ids: list, top_k: int = 5) -> list:
        """
        Find resolved queries similar to *query_text* from PostgreSQL and return
        the actual senior advice responses attached to them.

        Returns: list of {
            'query_text': str,          # the original student question
            'advice_content': str,      # the senior's written response
            'senior_name': str,
            'trust_score': float,
            'domain_ids': list,
            'resolved_at': str,
        }
        """
        from apps.query_orchestrator.models import Query, SeniorQueryAssignment

        # Find resolved queries (domain filtering done in Python to avoid
        # JSON __contains which is unsupported on SQLite)
        resolved_queries = list(
            Query.objects
            .filter(status='RESOLVED', is_resolved=True)
            .exclude(final_response='')
            .order_by('-timestamp')[:200]
        )

        # Filter to queries sharing at least one domain with the current query
        domain_set = {str(d) for d in domain_ids}
        resolved_queries = [
            rq for rq in resolved_queries
            if domain_set & {str(d) for d in (rq.domain_ids or [])}
        ]

        if not resolved_queries:
            return []

        # Rank candidates by embedding similarity (if Pinecone is available)
        query_embedding = self.embedding_gen.generate_query_embedding(query_text)
        scored = []
        for rq in resolved_queries:
            # Simple text-overlap score as baseline
            overlap = len(set(query_text.lower().split()) & set(rq.content.lower().split()))
            scored.append((rq, overlap))

        # Sort by word overlap descending, take top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top_queries = [rq for rq, _ in scored[:top_k]]

        # Collect all senior responses for those queries
        past_responses = []
        for rq in top_queries:
            assignments = SeniorQueryAssignment.objects.filter(
                query=rq, status='RESPONDED'
            ).exclude(advice_content='').select_related('senior')

            for assignment in assignments:
                past_responses.append({
                    'query_text': rq.content,
                    'advice_content': assignment.advice_content,
                    'senior_name': getattr(assignment.senior, 'name', 'Senior'),
                    'trust_score': float(assignment.trust_score_at_response or 0.0),
                    'domain_ids': rq.domain_ids,
                    'resolved_at': rq.timestamp.isoformat() if rq.timestamp else '',
                })

        # Sort by trust score descending
        past_responses.sort(key=lambda r: r['trust_score'], reverse=True)
        return past_responses[:top_k * 2]  # up to 2× top_k individual responses

    def generate_provisional_response(self, student_query: str, similar_cases: list,
                                       high_trust_advice: list,
                                       past_senior_responses: list = None) -> str:
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

        # Build past senior responses section
        senior_response_parts = []
        if past_senior_responses:
            for i, sr in enumerate(past_senior_responses[:5], 1):
                senior_response_parts.append(
                    f"Senior Response {i} (trust: {sr['trust_score']:.2f}, by {sr['senior_name']}):\n"
                    f"  Original Q: {sr['query_text'][:200]}\n"
                    f"  Expert Answer: {sr['advice_content']}"
                )
        senior_response_text = (
            "\n\n".join(senior_response_parts)
            if senior_response_parts
            else "No past expert responses found for similar questions."
        )

        prompt = f"""You are BEACON, an AI mentoring assistant. A student has asked a question.
Based on similar past questions, trusted senior advice, and verified expert responses to similar
questions from the past, provide a helpful and customized answer.

STUDENT QUESTION:
{student_query}

SIMILAR PAST CASES:
{context_text}

HIGH-TRUST SENIOR ADVICE:
{advice_text}

VERIFIED EXPERT RESPONSES TO SIMILAR PAST QUESTIONS:
{senior_response_text}

Instructions:
- Give the most weight to verified expert responses from seniors who answered similar questions before.
- Cross-reference their advice with the RAG-retrieved cases for consistency.
- Provide a clear, helpful, and personalized answer to the student.
- If multiple experts gave different but valid perspectives, mention the key viewpoints.
- End with a disclaimer that this is a provisional AI-generated response and a verified senior
  mentor will review and provide personalized guidance soon."""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"[RAGEngine] Gemini API error: {e}")
            return (
                "[Provisional answer unavailable — AI service is temporarily rate-limited. "
                "A senior mentor will provide guidance shortly.]"
            )


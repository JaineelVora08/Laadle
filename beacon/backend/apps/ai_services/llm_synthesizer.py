import json
from google import genai
from google.genai import types
from django.conf import settings


class LLMSynthesizer:
    """
    Weighted aggregation of multiple senior advice items.
    Weight formula: trust_score × similarity_score
    Uses Gemini 2.0 Flash for synthesis.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def compute_weight(self, trust_score: float, similarity_score: float) -> float:
        """Returns: weight float (product of trust and similarity)."""
        return trust_score * similarity_score

    def synthesize(self, student_query: str, advice_list: list) -> dict:
        """
        advice_list items: { content, senior_id, trust_score, similarity_score }
        Builds LLM prompt, calls Gemini, returns synthesized answer.
        Returns: { final_answer, agreements, disagreements }
        """
        if not advice_list:
            return {
                'final_answer': 'No senior responses received yet.',
                'agreements': [],
                'disagreements': []
            }

        # Compute weights and sort descending
        weighted_advice = []
        for advice in advice_list:
            weight = self.compute_weight(
                advice.get('trust_score', 0.5),
                advice.get('similarity_score', 0.5)
            )
            weighted_advice.append({**advice, 'weight': weight})
        weighted_advice.sort(key=lambda x: x['weight'], reverse=True)

        # Build prompt
        advice_text = ""
        for i, a in enumerate(weighted_advice, 1):
            advice_text += (
                f"\nAdvisor {i} (weight: {a['weight']:.3f}, trust: {a['trust_score']:.2f}):\n"
                f"{a['content']}\n"
            )

        prompt = f"""You are BEACON's synthesis engine. Multiple senior mentors have provided advice
for a student's question. Synthesize their responses into a single coherent answer.

STUDENT QUESTION: {student_query}

SENIOR RESPONSES (ordered by weight/trustworthiness):
{advice_text}

Instructions:
1. Synthesize a final comprehensive answer, weighting higher-trust responses more heavily
2. Identify key points where advisors AGREE
3. Identify any points where advisors DISAGREE

You MUST respond in EXACTLY this JSON format:
{{
  "final_answer": "Your synthesized answer here",
  "agreements": ["point 1 they agree on", "point 2"],
  "disagreements": ["point where they disagree, if any"]
}}"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                    max_output_tokens=800,
                )
            )
        except Exception as e:
            print(f"[LLMSynthesizer] Gemini API error during synthesis: {e}")
            # Fallback: use the highest-weighted senior's advice directly
            best = weighted_advice[0]['content'] if weighted_advice else 'No advice available.'
            return {
                'final_answer': best,
                'agreements': [],
                'disagreements': []
            }

        try:
            result = json.loads(response.text)
            return {
                'final_answer': result.get('final_answer', ''),
                'agreements': result.get('agreements', []),
                'disagreements': result.get('disagreements', [])
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                'final_answer': response.text if hasattr(response, 'text') else '',
                'agreements': [],
                'disagreements': []
            }

    def generate_followup_questions(self, query_content: str, domain_id: str, historical_followups: list = None) -> list:
        """
        Generates predictive follow-up questions the student might ask next.
        Uses historical_followups from similar past queries if provided.
        Returns: list of question strings (max 3)
        """
        history_text = ""
        if historical_followups:
            history_text = "\nStudents who asked similar questions often followed up with:\n- " + "\n- ".join(historical_followups[:5])

        prompt = f"""Based on this student question, predict 3 follow-up questions they might ask next.
Keep questions specific and actionable.{history_text}

Student question: {query_content}

You MUST respond in EXACTLY this JSON format:
{{"questions": ["question 1", "question 2", "question 3"]}}"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.5,
                    max_output_tokens=200,
                )
            )
        except Exception as e:
            print(f"[LLMSynthesizer] Gemini API error during followup generation: {e}")
            return []

        try:
            result = json.loads(response.text)
            if isinstance(result, dict) and 'questions' in result:
                return result['questions'][:3]
            if isinstance(result, list):
                return result[:3]
            return list(result.values())[0][:3] if result else []
        except (json.JSONDecodeError, IndexError, KeyError, AttributeError):
            return []

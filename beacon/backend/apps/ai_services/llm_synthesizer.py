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

    def categorize_advice(self, student_query: str, advice_list: list) -> dict:
        """
        Groups senior advice into opinion clusters using LLM.
        advice_list items: { senior_id, content, trust_score }
        Returns: {
            'groups': [{'label': str, 'senior_ids': [str], 'avg_trust': float}],
            'majority_group': {'label': str, 'senior_ids': [str], 'avg_trust': float},
            'minority_groups': [{'label': str, 'senior_ids': [str], 'avg_trust': float}]
        }
        """
        if not advice_list:
            return {'groups': [], 'majority_group': None, 'minority_groups': []}

        if len(advice_list) == 1:
            group = {
                'label': 'Single response',
                'senior_ids': [advice_list[0]['senior_id']],
                'avg_trust': advice_list[0].get('trust_score', 0.5),
            }
            return {'groups': [group], 'majority_group': group, 'minority_groups': []}

        # Build advisor text for prompt
        advisor_text = ""
        id_map = {}
        for i, a in enumerate(advice_list, 1):
            advisor_text += f"\nAdvisor {i} (ID: {a['senior_id']}):\n{a['content']}\n"
            id_map[a['senior_id']] = a

        prompt = f"""You are an advice categorizer. Multiple mentors responded to a student question.
Group their advice into opinion clusters — advisors who give essentially the same recommendation
belong in the same group.

STUDENT QUESTION: {student_query}

ADVISOR RESPONSES:
{advisor_text}

Instructions:
- Group advisors whose core recommendation is the same (even if worded differently)
- Give each group a short descriptive label
- Every advisor ID must appear in exactly one group

You MUST respond in EXACTLY this JSON format:
{{"groups": [{{"label": "short description", "senior_ids": ["id1", "id2"]}}]}}"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=400,
                )
            )
            result = json.loads(response.text)
            groups = result.get('groups', [])
        except Exception as e:
            print(f"[LLMSynthesizer] categorize_advice error: {e}")
            # Fallback: all in one group
            group = {
                'label': 'All responses',
                'senior_ids': [a['senior_id'] for a in advice_list],
                'avg_trust': sum(a.get('trust_score', 0.5) for a in advice_list) / len(advice_list),
            }
            return {'groups': [group], 'majority_group': group, 'minority_groups': []}

        # Enrich groups with avg_trust
        for g in groups:
            trust_scores = [
                id_map[sid].get('trust_score', 0.5)
                for sid in g['senior_ids']
                if sid in id_map
            ]
            g['avg_trust'] = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0

        # Determine majority: largest group, ties broken by highest avg_trust
        groups.sort(key=lambda g: (len(g['senior_ids']), g['avg_trust']), reverse=True)
        majority_group = groups[0] if groups else None
        minority_groups = groups[1:] if len(groups) > 1 else []

        return {
            'groups': groups,
            'majority_group': majority_group,
            'minority_groups': minority_groups,
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

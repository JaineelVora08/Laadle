class LLMSynthesizer:
    """
    Weighted aggregation of multiple senior advice items.
    Weight formula: trust_score × similarity_score
    """

    def compute_weight(self, trust_score: float, similarity_score: float) -> float:
        """
        Returns: weight float
        """
        pass

    def synthesize(self, student_query: str, advice_list: list) -> dict:
        """
        advice_list items: { content, senior_id, trust_score, similarity_score }
        Builds LLM prompt, calls API, extracts agreements/disagreements.
        Returns: SynthesizedAdviceResponse { final_answer, agreements, disagreements }
        """
        pass

    def generate_followup_questions(self, query_content: str, domain_id: str) -> list:
        """
        Analyzes historical interaction patterns, generates likely follow-up questions.
        Returns: list of question strings (max 3)
        """
        pass

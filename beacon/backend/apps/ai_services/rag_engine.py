class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    Retrieves similar past Q&A pairs from Pinecone, feeds to LLM for provisional answer.
    """

    def retrieve_similar_cases(self, query_embedding: list, domain_id: str) -> list:
        """
        Queries Pinecone filtered by domain_id.
        Returns: list of { query_text, advice_text, trust_score, senior_id }
        """
        pass

    def generate_provisional_response(self, student_query: str, similar_cases: list, high_trust_advice: list) -> str:
        """
        Builds prompt from retrieved context + high-trust advice.
        Calls LLM API.
        Returns: provisional answer string (includes disclaimer)
        """
        pass

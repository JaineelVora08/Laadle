class InternalQueryClient:
    """
    Used internally to interact with the query orchestrator from other services.
    """

    def submit_query(self, student_id: str, domain_id: str, content: str) -> dict:
        """
        POST /internal/query/submit/
        Returns: QuerySubmitResponse dict
        """
        pass

    def get_query_status(self, query_id: str) -> dict:
        """
        GET /internal/query/<query_id>/status/
        Returns: QueryStatusResponse dict
        """
        pass

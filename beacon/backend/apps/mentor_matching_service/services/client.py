class InternalMentorMatchingClient:
    """
    Used internally to trigger mentor matching from other services.
    """

    def find_mentors(self, student_id: str, domain_id: str, priority: int) -> list:
        """
        POST /internal/mentor-matching/find/
        Returns: list of MentorMatchResponse dicts
        """
        pass

    def create_mentorship(self, student_id: str, senior_id: str, domain_id: str) -> dict:
        """
        POST /internal/mentor-matching/connect/
        Returns: { mentorship_id, status }
        """
        pass

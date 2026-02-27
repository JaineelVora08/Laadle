class InternalProfileClient:
    """
    Used internally to fetch/update profile data across services.
    """

    def get_profile(self, user_id: str) -> dict:
        """
        GET /internal/profile/<user_id>/
        Returns: UserProfileResponse dict
        """
        pass

    def update_profile(self, user_id: str, data: dict) -> dict:
        """
        PATCH /internal/profile/<user_id>/
        Returns: Updated UserProfileResponse dict
        """
        pass

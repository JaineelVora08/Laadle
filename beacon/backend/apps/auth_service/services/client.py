class InternalUserClient:
    """
    Used by other modules (Module 2, 3) to fetch user data internally.
    Calls Module 1 (auth/user_profile_service) via X-Internal-Secret header.
    """

    def get_user(self, user_id: str) -> dict:
        """
        GET /internal/users/<user_id>/
        Returns: UserProfileResponse dict
        """
        pass

    def increment_senior_load(self, senior_id: str) -> dict:
        """
        PATCH /internal/users/<senior_id>/increment-load/
        Returns: { senior_id, new_active_load }
        """
        pass

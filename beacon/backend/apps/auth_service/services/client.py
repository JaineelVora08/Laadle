import json
import os
from urllib import request


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
        base_url = os.getenv('INTERNAL_BASE_URL', 'http://localhost:8000').rstrip('/')
        req = request.Request(
            url=f'{base_url}/internal/users/{user_id}/',
            headers={'X-Internal-Secret': os.getenv('INTERNAL_SECRET', 'internal_shared_secret')},
            method='GET',
        )
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))

    def increment_senior_load(self, senior_id: str) -> dict:
        """
        PATCH /internal/users/<senior_id>/increment-load/
        Returns: { senior_id, new_active_load }
        """
        base_url = os.getenv('INTERNAL_BASE_URL', 'http://localhost:8000').rstrip('/')
        payload = json.dumps({'delta': 1}).encode('utf-8')
        req = request.Request(
            url=f'{base_url}/internal/users/{senior_id}/increment-load/',
            data=payload,
            headers={
                'X-Internal-Secret': os.getenv('INTERNAL_SECRET', 'internal_shared_secret'),
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))

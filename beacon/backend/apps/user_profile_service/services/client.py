import json
import os
from urllib import request


class InternalProfileClient:
    """
    Used internally to fetch/update profile data across services.
    """

    def get_profile(self, user_id: str) -> dict:
        """
        GET /internal/profile/<user_id>/
        Returns: UserProfileResponse dict
        """
        base_url = os.getenv('INTERNAL_BASE_URL', 'http://localhost:8000').rstrip('/')
        req = request.Request(
            url=f'{base_url}/internal/profile/{user_id}/',
            headers={'X-Internal-Secret': os.getenv('INTERNAL_SECRET', 'internal_shared_secret')},
            method='GET',
        )
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))

    def update_profile(self, user_id: str, data: dict) -> dict:
        """
        PATCH /internal/profile/<user_id>/
        Returns: Updated UserProfileResponse dict
        """
        base_url = os.getenv('INTERNAL_BASE_URL', 'http://localhost:8000').rstrip('/')
        payload = json.dumps(data).encode('utf-8')
        req = request.Request(
            url=f'{base_url}/internal/profile/{user_id}/',
            data=payload,
            headers={
                'X-Internal-Secret': os.getenv('INTERNAL_SECRET', 'internal_shared_secret'),
                'Content-Type': 'application/json',
            },
            method='PATCH',
        )
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))

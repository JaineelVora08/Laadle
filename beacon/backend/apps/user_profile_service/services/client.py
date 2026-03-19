import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, 'INTERNAL_SERVICE_BASE_URL', 'http://localhost:8000')
INTERNAL_SECRET = getattr(settings, 'INTERNAL_SECRET', '')


class InternalProfileClient:
    """
    Used internally to fetch/update profile data across services.
    """

    def __init__(self):
        self.headers = {'X-Internal-Secret': INTERNAL_SECRET}

    def get_profile(self, user_id: str) -> dict:
        """
        GET /internal/profile/<user_id>/
        Returns: UserProfileResponse dict
        """
        try:
            url = f'{BASE_URL}/internal/profile/{user_id}/'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error('InternalProfileClient.get_profile failed: %s', exc)
            return {}

    def update_profile(self, user_id: str, data: dict) -> dict:
        """
        PATCH /internal/profile/<user_id>/
        Returns: Updated UserProfileResponse dict
        """
        try:
            url = f'{BASE_URL}/internal/profile/{user_id}/'
            response = requests.patch(
                url, json=data,
                headers={**self.headers, 'Content-Type': 'application/json'},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error('InternalProfileClient.update_profile failed: %s', exc)
            return {}

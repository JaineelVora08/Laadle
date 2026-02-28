import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, 'INTERNAL_SERVICE_BASE_URL', 'http://localhost:8000')
INTERNAL_SECRET = getattr(settings, 'INTERNAL_SECRET', '')


class InternalMentorMatchingClient:
    """
    Used internally to trigger mentor matching from other services.
    Called by query_orchestrator to find and connect mentors.
    """

    def __init__(self):
        self.headers = {
            'X-Internal-Secret': INTERNAL_SECRET,
            'Content-Type': 'application/json',
        }

    def find_mentors(self, student_id: str, domain_id: str, priority: int) -> list:
        """
        POST /internal/mentor-matching/find/
        Returns: list of MentorMatchResponse dicts
        """
        try:
            url = f'{BASE_URL}/api/internal/mentor-matching/find/'
            payload = {
                'student_id': student_id,
                'domain_id': domain_id,
                'priority': priority,
            }
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error('InternalMentorMatchingClient.find_mentors failed: %s', exc)
            return []

    def create_mentorship(self, student_id: str, senior_id: str, domain_id: str) -> dict:
        """
        POST /internal/mentor-matching/connect/
        Returns: { mentorship_id, status }
        """
        try:
            url = f'{BASE_URL}/api/internal/mentor-matching/connect/'
            payload = {
                'student_id': student_id,
                'senior_id': senior_id,
                'domain_id': domain_id,
            }
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error('InternalMentorMatchingClient.create_mentorship failed: %s', exc)
            return {}

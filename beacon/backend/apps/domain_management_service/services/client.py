import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, 'INTERNAL_SERVICE_BASE_URL', 'http://localhost:8000')
INTERNAL_SECRET = getattr(settings, 'INTERNAL_SECRET', '')


class InternalDomainClient:
    """
    Used internally to interact with domain management service.
    Called by other modules (e.g., query_orchestrator) to fetch domain data.
    """

    def __init__(self):
        self.headers = {'X-Internal-Secret': INTERNAL_SECRET}

    def get_user_domains(self, user_id: str) -> list:
        """
        GET /internal/domains/user/<user_id>/
        Returns: list of DomainLinkResponse dicts
        """
        try:
            url = f'{BASE_URL}/api/domains/internal/user/{user_id}/'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error('InternalDomainClient.get_user_domains failed: %s', exc)
            return []

    def get_domain(self, domain_id: str) -> dict:
        """
        GET /internal/domains/<domain_id>/
        Returns: DomainNode dict
        """
        try:
            url = f'{BASE_URL}/api/domains/internal/{domain_id}/'
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.error('InternalDomainClient.get_domain failed: %s', exc)
            return {}

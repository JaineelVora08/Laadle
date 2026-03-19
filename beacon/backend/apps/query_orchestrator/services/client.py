import requests
from django.conf import settings


class InternalQueryClient:
    """
    Used internally to interact with the query orchestrator from other services.
    """
    BASE_URL = 'http://localhost:8000'

    def _headers(self):
        return {'X-Internal-Secret': settings.INTERNAL_SECRET}

    def submit_query(self, student_id: str, domain_id: str, content: str) -> dict:
        """
        POST /api/query/submit/
        Returns: QuerySubmitResponse dict
        """
        response = requests.post(
            f'{self.BASE_URL}/api/query/submit/',
            json={
                'student_id': student_id,
                'domain_id': domain_id,
                'content': content
            },
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    def get_query_status(self, query_id: str) -> dict:
        """
        GET /api/query/<query_id>/status/
        Returns: QueryStatusResponse dict
        """
        response = requests.get(
            f'{self.BASE_URL}/api/query/{query_id}/status/',
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

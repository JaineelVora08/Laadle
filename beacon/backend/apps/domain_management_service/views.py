from rest_framework.views import APIView


class AddDomainView(APIView):
    """
    POST /api/domains/add/
    Input:  { user_id, raw_interest_text }
    Output: DomainLinkResponse
    Calls:  ai_services — POST /internal/embeddings/generate/
            Neo4j — cosine similarity check, create/link DomainNode
    """
    def post(self, request):
        pass


class UserDomainsView(APIView):
    """
    GET /api/domains/user/<user_id>/
    Output: list of DomainLinkResponse
    """
    def get(self, request, user_id):
        pass


class AllDomainsView(APIView):
    """
    GET /api/domains/all/
    Output: list of all DomainNode records
    """
    def get(self, request):
        pass

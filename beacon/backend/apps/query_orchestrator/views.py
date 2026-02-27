from rest_framework.views import APIView


class SubmitQueryView(APIView):
    """
    POST /api/query/submit/
    Input:  QuerySubmitRequest { student_id, domain_id, content }
    Output: QuerySubmitResponse
    Calls:  QueryOrchestrator.handle_new_query()
    """
    def post(self, request):
        pass


class QueryStatusView(APIView):
    """
    GET /api/query/<query_id>/status/
    Output: QueryStatusResponse { query_id, status, provisional_answer, final_answer }
    """
    def get(self, request, query_id):
        pass


class SeniorResponseView(APIView):
    """
    POST /api/query/<query_id>/senior-response/
    Input:  SeniorResponseRequest
    Output: FinalAdviceResponse
    Calls:  QueryOrchestrator.handle_senior_response()
    """
    def post(self, request, query_id):
        pass


class SeniorPendingQueriesView(APIView):
    """
    GET /api/query/pending/senior/<senior_id>/
    Output: list of pending QuerySubmitResponse objects for this senior
    """
    def get(self, request, senior_id):
        pass

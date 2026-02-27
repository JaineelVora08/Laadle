from rest_framework.views import APIView


class RecalculateTrustView(APIView):
    """
    POST /internal/trust-score/recalculate/
    Input:  { senior_id }
    Output: { senior_id, new_trust_score }
    Calls:  TrustScoreCalculator.compute()
    Called by: Module 1 (after achievement upload)
    """
    def post(self, request):
        pass


class UpdateFeedbackView(APIView):
    """
    POST /internal/trust-score/update-feedback/
    Input:  TrustUpdateRequest
    Output: { senior_id, new_trust_score }
    Calls:  TrustScoreCalculator.update_feedback()
    Called by: Module 3 (after query resolution)
    """
    def post(self, request):
        pass

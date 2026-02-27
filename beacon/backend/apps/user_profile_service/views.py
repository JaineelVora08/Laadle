from rest_framework.views import APIView


class UserProfileView(APIView):
    """
    GET  /api/profile/<user_id>/
    Output: UserProfileResponse
    Calls:  Nothing
    """
    def get(self, request, user_id):
        pass


class UpdateProfileView(APIView):
    """
    PUT /api/profile/<user_id>/update/
    Input:  Partial UserProfileResponse fields
    Output: Updated UserProfileResponse
    """
    def put(self, request, user_id):
        pass


class AchievementView(APIView):
    """
    POST /api/profile/<user_id>/achievements/
    Input:  { title, proof_url }
    Output: { id, title, proof_url, verified: false }
    Calls:  trust_score_service — POST /internal/trust-score/recalculate/
    """
    def post(self, request, user_id):
        pass

    def get(self, request, user_id):
        pass

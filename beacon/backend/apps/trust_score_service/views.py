from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.auth_service.models import User
from .calculator import TrustScoreCalculator
from .serializers import TrustScoreResponseSerializer, TrustUpdateRequestSerializer


class RecalculateTrustView(APIView):
    """
    POST /internal/trust-score/recalculate/
    Input:  { senior_id }
    Output: { senior_id, new_trust_score }
    Calls:  TrustScoreCalculator.compute()
    Called by: Module 1 (after achievement upload)
    """
    def post(self, request):
        senior_id = request.data.get('senior_id')
        if not senior_id:
            return Response({'senior_id': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(id=senior_id, role='SENIOR').exists():
            return Response({'detail': 'Senior not found.'}, status=status.HTTP_404_NOT_FOUND)

        calculator = TrustScoreCalculator()
        new_score = calculator.compute(senior_id)
        response_data = {'senior_id': senior_id, 'new_trust_score': new_score}
        serializer = TrustScoreResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateFeedbackView(APIView):
    """
    POST /internal/trust-score/update-feedback/
    Input:  TrustUpdateRequest
    Output: { senior_id, new_trust_score }
    Calls:  TrustScoreCalculator.update_feedback()
    Called by: Module 3 (after query resolution)
    """
    def post(self, request):
        request_serializer = TrustUpdateRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        payload = request_serializer.validated_data
        senior_id = payload['senior_id']

        if not User.objects.filter(id=senior_id, role='SENIOR').exists():
            return Response({'detail': 'Senior not found.'}, status=status.HTTP_404_NOT_FOUND)

        calculator = TrustScoreCalculator()
        result = calculator.update_feedback(senior_id=senior_id, feedback_data=payload)

        response_serializer = TrustScoreResponseSerializer(data=result)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

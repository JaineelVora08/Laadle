from rest_framework import serializers


class TrustUpdateRequestSerializer(serializers.Serializer):
    """Serializes TrustUpdateRequest: senior_id, student_feedback_score, follow_through_rate."""
    pass


class TrustScoreResponseSerializer(serializers.Serializer):
    """Serializes trust score response: senior_id, new_trust_score."""
    pass

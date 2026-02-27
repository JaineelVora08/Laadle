from rest_framework import serializers


class QuerySubmitRequestSerializer(serializers.Serializer):
    """Serializes QuerySubmitRequest: student_id, domain_id, content."""
    pass


class QuerySubmitResponseSerializer(serializers.Serializer):
    """Serializes QuerySubmitResponse: query_id, status, provisional_answer, follow_up_questions."""
    pass


class SeniorResponseRequestSerializer(serializers.Serializer):
    """Serializes SeniorResponseRequest: senior_id, advice_content, answered_followups."""
    pass


class FinalAdviceResponseSerializer(serializers.Serializer):
    """Serializes FinalAdviceResponse: query_id, final_answer, agreements, disagreements, conflict_detected."""
    pass


class QueryStatusResponseSerializer(serializers.Serializer):
    """Serializes QueryStatusResponse: query_id, status, provisional_answer, final_answer."""
    pass

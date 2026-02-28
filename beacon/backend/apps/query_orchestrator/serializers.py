from rest_framework import serializers


class QuerySubmitRequestSerializer(serializers.Serializer):
    """Validates QuerySubmitRequest."""
    student_id = serializers.UUIDField()
    domain_id = serializers.CharField()
    content = serializers.CharField()


class QuerySubmitResponseSerializer(serializers.Serializer):
    """Serializes QuerySubmitResponse."""
    query_id = serializers.UUIDField()
    status = serializers.CharField()
    content = serializers.CharField(required=False, allow_blank=True)
    provisional_answer = serializers.CharField(allow_blank=True)
    follow_up_questions = serializers.ListField(child=serializers.CharField())
    matched_seniors = serializers.ListField(child=serializers.UUIDField())
    timestamp = serializers.DateTimeField()


class AnsweredFollowupSerializer(serializers.Serializer):
    """Nested serializer for follow-up Q&A pairs."""
    question = serializers.CharField()
    answer = serializers.CharField()


class SeniorResponseRequestSerializer(serializers.Serializer):
    """Validates SeniorResponse Step 1: Main Advice."""
    senior_id = serializers.UUIDField()
    advice_content = serializers.CharField()


class SeniorResponseStep1ResponseSerializer(serializers.Serializer):
    """Serializes response for SeniorResponse Step 1."""
    query_id = serializers.UUIDField()
    status = serializers.CharField()
    predicted_faqs = serializers.ListField(child=serializers.CharField())


class SeniorFAQResponseRequestSerializer(serializers.Serializer):
    """Validates SeniorResponse Step 2: FAQ Answers."""
    senior_id = serializers.UUIDField()
    faq_answers = AnsweredFollowupSerializer(many=True)


class ContributingSeniorSerializer(serializers.Serializer):
    """Nested serializer for contributing seniors."""
    senior_id = serializers.UUIDField()
    trust_score = serializers.FloatField()
    weight = serializers.FloatField()


class FinalAdviceResponseSerializer(serializers.Serializer):
    """Serializes FinalAdviceResponse."""
    query_id = serializers.UUIDField()
    final_answer = serializers.CharField()
    agreements = serializers.ListField(child=serializers.CharField())
    disagreements = serializers.ListField(child=serializers.CharField())
    conflict_detected = serializers.BooleanField()
    conflict_details = serializers.CharField(allow_null=True)
    contributing_seniors = ContributingSeniorSerializer(many=True)


class QueryStatusResponseSerializer(serializers.Serializer):
    """Serializes QueryStatusResponse."""
    query_id = serializers.UUIDField()
    status = serializers.CharField()
    provisional_answer = serializers.CharField(allow_null=True)
    final_answer = serializers.CharField(allow_null=True)
    follow_up_questions = serializers.ListField(child=serializers.CharField())
    conflict_detected = serializers.BooleanField()


class FollowUpRequestSerializer(serializers.Serializer):
    """Validates FollowUpRequest."""
    student_id = serializers.UUIDField()
    content = serializers.CharField()


class FollowUpResponseSerializer(serializers.Serializer):
    """Serializes FollowUpResponse."""
    answer = serializers.CharField(allow_null=True)
    source = serializers.CharField()
    confidence = serializers.FloatField(required=False)
    disclaimer = serializers.CharField(required=False)
    message = serializers.CharField(required=False)

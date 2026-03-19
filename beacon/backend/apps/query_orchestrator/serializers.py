from rest_framework import serializers


class QuerySubmitRequestSerializer(serializers.Serializer):
    """Validates QuerySubmitRequest. Accepts domain_ids (list) or domain_id (single, backward compat)."""
    student_id = serializers.UUIDField()
    domain_ids = serializers.ListField(child=serializers.CharField(), required=False)
    domain_id = serializers.CharField(required=False)
    content = serializers.CharField()

    def validate(self, data):
        # Accept either domain_ids or domain_id, normalize to domain_ids
        domain_ids = data.get('domain_ids')
        domain_id = data.get('domain_id')
        if not domain_ids and not domain_id:
            raise serializers.ValidationError('Either domain_ids or domain_id is required.')
        if not domain_ids:
            domain_ids = [domain_id]
        data['domain_ids'] = domain_ids
        return data


class QuerySubmitResponseSerializer(serializers.Serializer):
    """Serializes QuerySubmitResponse."""
    query_id = serializers.UUIDField()
    content = serializers.CharField(required=False, allow_blank=True, default='')
    status = serializers.CharField()
    provisional_answer = serializers.CharField(allow_blank=True)
    follow_up_questions = serializers.ListField(child=serializers.CharField())
    matched_seniors = serializers.ListField(child=serializers.UUIDField())
    timestamp = serializers.DateTimeField()
    cluster_id = serializers.UUIDField(required=False, allow_null=True)
    cluster_student_count = serializers.IntegerField(required=False, default=0)


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
    in_majority = serializers.BooleanField(required=False, default=True)


class FinalAdviceResponseSerializer(serializers.Serializer):
    """Serializes FinalAdviceResponse."""
    query_id = serializers.UUIDField()
    final_answer = serializers.CharField()
    agreements = serializers.ListField(child=serializers.CharField())
    disagreements = serializers.ListField(child=serializers.CharField())
    majority_label = serializers.CharField(allow_null=True, required=False)
    opinion_groups = serializers.ListField(required=False, default=[])
    anomaly_detected = serializers.BooleanField(required=False, default=False)
    anomaly_warning = serializers.CharField(allow_null=True, required=False)
    conflict_detected = serializers.BooleanField()
    conflict_details = serializers.CharField(allow_null=True)
    contributing_seniors = ContributingSeniorSerializer(many=True)
    finalized_by = serializers.CharField(required=False, allow_null=True)
    total_responses_considered = serializers.IntegerField(required=False)
    majority_count = serializers.IntegerField(required=False)
    auto_finalized = serializers.BooleanField(required=False, default=False)


class QueryStatusResponseSerializer(serializers.Serializer):
    """Serializes QueryStatusResponse."""
    query_id = serializers.UUIDField()
    content = serializers.CharField(required=False, allow_blank=True, default='')
    status = serializers.CharField()
    is_resolved = serializers.BooleanField(required=False, default=False)
    provisional_answer = serializers.CharField(allow_null=True)
    final_answer = serializers.CharField(allow_null=True)
    follow_up_questions = serializers.ListField(child=serializers.CharField())
    conflict_detected = serializers.BooleanField()
    conflict_details = serializers.CharField(allow_null=True, required=False)
    contributing_seniors = ContributingSeniorSerializer(many=True, required=False)
    student_rating = serializers.IntegerField(allow_null=True, required=False)
    follow_through_success = serializers.BooleanField(allow_null=True, required=False)
    follow_through_proof = serializers.CharField(allow_blank=True, required=False, default='')
    cluster_id = serializers.UUIDField(required=False, allow_null=True)
    cluster_student_count = serializers.IntegerField(required=False, default=0)
    # Majority mechanism fields
    total_assigned = serializers.IntegerField(required=False, default=0)
    responses_received = serializers.IntegerField(required=False, default=0)
    faq_completed_count = serializers.IntegerField(required=False, default=0)
    response_deadline = serializers.DateTimeField(required=False, allow_null=True)
    deadline_passed = serializers.BooleanField(required=False, default=False)
    time_remaining_seconds = serializers.FloatField(required=False, allow_null=True)
    can_finalize = serializers.BooleanField(required=False, default=False)
    finalized_by = serializers.CharField(required=False, allow_null=True)


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


class StudentRatingRequestSerializer(serializers.Serializer):
    """Validates student rating request (1-5 stars)."""
    student_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5)


class FollowThroughRequestSerializer(serializers.Serializer):
    """Validates follow-through success report."""
    student_id = serializers.UUIDField()
    success = serializers.BooleanField()
    proof_url = serializers.URLField(required=False, allow_blank=True, default='')


class FinalizeRequestSerializer(serializers.Serializer):
    """Validates student early-finalization request."""
    student_id = serializers.UUIDField()


class SeniorFAQStep2ResponseSerializer(serializers.Serializer):
    """Response when senior FAQ is recorded but query is NOT yet finalized."""
    query_id = serializers.UUIDField()
    status = serializers.CharField()
    responses_received = serializers.IntegerField()
    faq_completed_count = serializers.IntegerField()
    total_assigned = serializers.IntegerField()
    auto_finalized = serializers.BooleanField(default=False)
    message = serializers.CharField(required=False, allow_blank=True)


class ResponseStatusSerializer(serializers.Serializer):
    """Serializes query response status for majority mechanism."""
    query_id = serializers.UUIDField()
    status = serializers.CharField()
    total_assigned = serializers.IntegerField()
    responses_received = serializers.IntegerField()
    faq_completed_count = serializers.IntegerField()
    response_deadline = serializers.DateTimeField(allow_null=True)
    deadline_passed = serializers.BooleanField()
    time_remaining_seconds = serializers.FloatField(allow_null=True)
    can_finalize = serializers.BooleanField()
    finalized_by = serializers.CharField(allow_null=True)

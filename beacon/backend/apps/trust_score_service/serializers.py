from rest_framework import serializers


class TrustUpdateRequestSerializer(serializers.Serializer):
    """Serializes TrustUpdateRequest: senior_id, student_feedback_score, follow_through_rate."""
    senior_id = serializers.CharField()
    student_feedback_score = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)
    follow_through_rate = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)
    achievement_weight = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)
    n_success = serializers.IntegerField(required=False, min_value=0)
    n_total = serializers.IntegerField(required=False, min_value=0)
    days_inactive = serializers.IntegerField(required=False, min_value=0)
    reply_time_hours = serializers.FloatField(required=False, min_value=0.0)
    is_majority = serializers.BooleanField(required=False)
    M = serializers.IntegerField(required=False, min_value=0)
    m = serializers.IntegerField(required=False, min_value=0)
    N = serializers.IntegerField(required=False, min_value=1)
    contextual_V = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)
    query_embedding = serializers.ListField(
        child=serializers.FloatField(), required=False, allow_empty=False
    )
    achievement_embedding = serializers.ListField(
        child=serializers.FloatField(), required=False, allow_empty=False
    )
    success_rate_score = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)
    verified_achievement_score = serializers.FloatField(required=False, min_value=0.0, max_value=100.0)

    def validate(self, attrs):
        n_success = attrs.get('n_success')
        n_total = attrs.get('n_total')
        if n_success is not None and n_total is not None and n_success > n_total:
            raise serializers.ValidationError({'n_success': 'n_success cannot be greater than n_total.'})

        is_majority = attrs.get('is_majority')
        if is_majority is False:
            missing = [key for key in ('M', 'm', 'N') if key not in attrs]
            if missing:
                raise serializers.ValidationError({
                    'alignment': f"Missing required fields for non-majority update: {', '.join(missing)}"
                })

        query_embedding = attrs.get('query_embedding')
        achievement_embedding = attrs.get('achievement_embedding')
        if (query_embedding is None) != (achievement_embedding is None):
            raise serializers.ValidationError(
                {'embeddings': 'Both query_embedding and achievement_embedding are required together.'}
            )

        if query_embedding is not None and len(query_embedding) != len(achievement_embedding):
            raise serializers.ValidationError(
                {'embeddings': 'query_embedding and achievement_embedding must have the same length.'}
            )

        if attrs.get('verified_achievement_score') is not None and attrs.get('achievement_weight') is None:
            attrs['achievement_weight'] = attrs['verified_achievement_score']

        if attrs.get('success_rate_score') is not None and attrs.get('follow_through_rate') is None:
            attrs['follow_through_rate'] = attrs['success_rate_score']

        return attrs


class TrustScoreResponseSerializer(serializers.Serializer):
    """Serializes trust score response: senior_id, new_trust_score."""
    senior_id = serializers.CharField()
    new_trust_score = serializers.FloatField(min_value=0.0, max_value=100.0)

from rest_framework import serializers


class AddDomainRequestSerializer(serializers.Serializer):
    """Validates input for POST /api/domains/add/."""
    user_id = serializers.CharField(required=True)
    raw_interest_text = serializers.CharField(required=True, max_length=500)
    priority = serializers.IntegerField(required=False, default=1, min_value=1, max_value=10)
    current_level = serializers.CharField(required=False, default='beginner')
    experience_level = serializers.CharField(required=False, default='intermediate')
    years_of_involvement = serializers.IntegerField(required=False, default=0, min_value=0)


class DomainLinkResponseSerializer(serializers.Serializer):
    """Serializes DomainLinkResponse: domain_id, name, type, priority, current_level."""
    domain_id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    priority = serializers.IntegerField()
    current_level = serializers.CharField()
    embedding_ref = serializers.CharField(required=False, default='', allow_blank=True)
    popularity_score = serializers.FloatField(required=False, default=0.0)


class DomainNodeSerializer(serializers.Serializer):
    """Serializes DomainNode: uid, name, type, embedding_ref, popularity_score."""
    uid = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()
    embedding_ref = serializers.CharField(allow_blank=True)
    popularity_score = serializers.FloatField()

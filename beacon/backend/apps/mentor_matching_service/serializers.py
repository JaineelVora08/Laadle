from rest_framework import serializers


class MentorMatchRequestSerializer(serializers.Serializer):
    """Serializes MentorMatchRequest: student_id, domain_id, priority."""
    student_id = serializers.CharField(required=True)
    domain_id = serializers.CharField(required=True)
    priority = serializers.IntegerField(required=False, default=1, min_value=1, max_value=10)


class MentorMatchResponseSerializer(serializers.Serializer):
    """Serializes MentorMatchResponse: senior_id, name, trust_score, domain, experience_level."""
    senior_id = serializers.CharField()
    name = serializers.CharField()
    trust_score = serializers.FloatField()
    domain = serializers.CharField()
    experience_level = serializers.CharField()
    availability = serializers.BooleanField()
    active_load = serializers.IntegerField()
    years_of_involvement = serializers.IntegerField(required=False, default=0)


class PeerMatchResponseSerializer(serializers.Serializer):
    """Serializes peer match response for junior-to-junior discovery."""
    student_id = serializers.CharField()
    name = serializers.CharField()
    domain = serializers.CharField()
    current_level = serializers.CharField()
    priority = serializers.IntegerField(required=False, default=1)
    shared_domains = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    shared_domain_count = serializers.IntegerField(required=False, default=0)
    similarity_score = serializers.FloatField(required=False, default=0.0)


class ConnectMentorRequestSerializer(serializers.Serializer):
    """Validates input for POST /api/mentor-matching/connect/."""
    student_id = serializers.CharField(required=True)
    senior_id = serializers.CharField(required=True)
    domain_id = serializers.CharField(required=True)


class FindPeerRequestSerializer(serializers.Serializer):
    """Validates input for POST /api/peer-matching/find/."""
    student_id = serializers.CharField(required=True)
    domain_id = serializers.CharField(required=False, allow_blank=False)
    top_k = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)

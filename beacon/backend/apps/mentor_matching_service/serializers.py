from rest_framework import serializers


class MentorMatchRequestSerializer(serializers.Serializer):
    """Serializes MentorMatchRequest: student_id, domain_id, priority."""
    pass


class MentorMatchResponseSerializer(serializers.Serializer):
    """Serializes MentorMatchResponse: senior_id, name, trust_score, domain, experience_level."""
    pass


class PeerMatchResponseSerializer(serializers.Serializer):
    """Serializes PeerMatchResponse: student_id, name, domain, current_level."""
    pass

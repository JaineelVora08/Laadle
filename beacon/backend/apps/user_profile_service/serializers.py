from rest_framework import serializers


class UserProfileResponseSerializer(serializers.Serializer):
    """Serializes UserProfileResponse."""
    pass


class AchievementSerializer(serializers.Serializer):
    """Serializes Achievement data: id, title, proof_url, verified."""
    pass

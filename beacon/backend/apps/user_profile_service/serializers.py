from rest_framework import serializers


class UserProfileResponseSerializer(serializers.Serializer):
    """Serializes UserProfileResponse."""
    id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=['STUDENT', 'SENIOR'])
    availability = serializers.BooleanField()
    trust_score = serializers.FloatField()
    current_level = serializers.CharField()
    active_load = serializers.IntegerField()
    low_energy_mode = serializers.BooleanField(allow_null=True)
    momentum_score = serializers.FloatField(allow_null=True)
    consistency_score = serializers.FloatField(allow_null=True)
    alignment_score = serializers.FloatField(allow_null=True)
    follow_through_rate = serializers.FloatField(allow_null=True)
    achievements = serializers.ListField(child=serializers.DictField(), default=list)


class AchievementSerializer(serializers.Serializer):
    """Serializes Achievement data: id, title, proof_url, verified."""
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(max_length=255)
    proof_url = serializers.URLField(required=False, allow_blank=True, default='')
    verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class UpdateProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    availability = serializers.BooleanField(required=False)
    current_level = serializers.CharField(max_length=100, required=False, allow_blank=True)

    low_energy_mode = serializers.BooleanField(required=False)
    momentum_score = serializers.FloatField(required=False)

    consistency_score = serializers.FloatField(required=False)
    alignment_score = serializers.FloatField(required=False)
    follow_through_rate = serializers.FloatField(required=False)

    def validate(self, attrs):
        role = self.context['role']
        student_fields = {'low_energy_mode', 'momentum_score'}
        senior_fields = {'consistency_score', 'alignment_score', 'follow_through_rate'}

        if role == 'STUDENT' and senior_fields.intersection(attrs.keys()):
            raise serializers.ValidationError('Senior-only fields cannot be updated for STUDENT users.')
        if role == 'SENIOR' and student_fields.intersection(attrs.keys()):
            raise serializers.ValidationError('Student-only fields cannot be updated for SENIOR users.')

        return attrs

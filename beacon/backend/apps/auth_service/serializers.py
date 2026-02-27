from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    """Validates registration input: name, email, password, role, current_level."""
    pass


class LoginSerializer(serializers.Serializer):
    """Validates login input: email, password."""
    pass


class AuthTokenResponseSerializer(serializers.Serializer):
    """Serializes AuthTokenResponse: access, refresh, user_id, role."""
    pass

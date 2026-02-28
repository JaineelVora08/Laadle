from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import serializers

from .models import User, Student, Senior


class RegisterSerializer(serializers.Serializer):
    """Validates registration input: name, email, password, role, current_level."""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    role = serializers.ChoiceField(choices=['STUDENT', 'SENIOR'])
    current_level = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')

    def validate_email(self, value):
        email = value.strip().lower()
        if not email.endswith('@iitj.ac.in'):
            raise serializers.ValidationError('Only IITJ college email IDs (@iitj.ac.in) are allowed.')
        return email

    def create(self, validated_data):
        role = validated_data['role']

        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data['email'],
                name=validated_data['name'],
                password=validated_data['password'],
                role=role,
                current_level=validated_data.get('current_level', ''),
            )

            if role == 'STUDENT':
                Student.objects.get_or_create(user=user)
            else:
                Senior.objects.get_or_create(user=user)

        return user


class LoginSerializer(serializers.Serializer):
    """Validates login input: email, password."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        email = value.strip().lower()
        if not email.endswith('@iitj.ac.in'):
            raise serializers.ValidationError('Only IITJ college email IDs (@iitj.ac.in) are allowed.')
        return email

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        attrs['user'] = user
        return attrs


class AuthTokenResponseSerializer(serializers.Serializer):
    """Serializes AuthTokenResponse: access, refresh, user_id, role."""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=['STUDENT', 'SENIOR'])


class GoogleLoginSerializer(serializers.Serializer):
    """Validates Google ID token, enforces IITJ domain, and returns/create local user."""
    id_token = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['STUDENT', 'SENIOR'], required=False, default='STUDENT')
    current_level = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')

    def validate(self, attrs):
        token = attrs.get('id_token')

        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
        except ImportError as exc:
            raise serializers.ValidationError(f'Google auth dependency is missing: {exc}')

        allowed_client_ids = getattr(settings, 'GOOGLE_OAUTH_CLIENT_IDS', [])
        if not allowed_client_ids:
            raise serializers.ValidationError('Google OAuth client ID is not configured.')

        try:
            payload = google_id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                None,
            )
        except Exception:
            raise serializers.ValidationError('Invalid Google ID token.')

        token_audience = payload.get('aud')
        token_authorized_party = payload.get('azp')
        if token_audience not in allowed_client_ids and token_authorized_party not in allowed_client_ids:
            raise serializers.ValidationError('Google token audience does not match configured client ID.')

        email = (payload.get('email') or '').strip().lower()
        name = (payload.get('name') or '').strip()
        email_verified = payload.get('email_verified', False)

        if not email or not email.endswith('@iitj.ac.in'):
            raise serializers.ValidationError('Only IITJ college email IDs (@iitj.ac.in) are allowed.')
        if not email_verified:
            raise serializers.ValidationError('Google email must be verified.')

        attrs['google_email'] = email
        attrs['google_name'] = name or email.split('@')[0]
        return attrs

    def create(self, validated_data):
        email = validated_data['google_email']
        name = validated_data['google_name']
        requested_role = validated_data.get('role', 'STUDENT')
        current_level = validated_data.get('current_level', '')

        with transaction.atomic():
            try:
                user = User.objects.get(email=email)
                created = False
            except User.DoesNotExist:
                user = User(
                    email=email,
                    name=name,
                    role=requested_role,
                    current_level=current_level,
                )
                user.set_unusable_password()
                user.save()
                created = True

            if not user.name:
                user.name = name
                user.save(update_fields=['name'])

            if user.role == 'STUDENT':
                Student.objects.get_or_create(user=user)
            else:
                Senior.objects.get_or_create(user=user)

        return user

from rest_framework.views import APIView
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    AuthTokenResponseSerializer,
    GoogleLoginSerializer,
    LoginSerializer,
    RegisterSerializer,
)
from .models import User


def _build_auth_payload(user):
    refresh = RefreshToken.for_user(user)
    payload = {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user_id': user.id,
        'role': user.role,
    }
    serializer = AuthTokenResponseSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _is_internal_request(request):
    return request.headers.get('X-Internal-Secret') == settings.INTERNAL_SECRET


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Input:  { name, email, password, role, current_level }
    Output: AuthTokenResponse
    Calls:  Nothing
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_build_auth_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Input:  { email, password }
    Output: AuthTokenResponse { access, refresh, user_id, role }
    Calls:  Nothing
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(_build_auth_payload(user), status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    """
    POST /api/auth/google/login/
    Input:  { id_token, role?, current_level? }
    Output: AuthTokenResponse { access, refresh, user_id, role }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(_build_auth_payload(user), status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """
    POST /api/auth/token/refresh/
    Input:  { refresh }
    Output: { access }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Invalid or expired refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


class InternalUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        if not _is_internal_request(request):
            return Response({'detail': 'Unauthorized internal request.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        payload = {
            'id': str(user.id),
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'availability': user.availability,
            'active_load': user.active_load,
            'trust_score': user.trust_score,
        }
        return Response(payload, status=status.HTTP_200_OK)


class InternalIncrementSeniorLoadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, senior_id):
        if not _is_internal_request(request):
            return Response({'detail': 'Unauthorized internal request.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            senior = User.objects.get(id=senior_id)
        except User.DoesNotExist:
            return Response({'detail': 'Senior user not found.'}, status=status.HTTP_404_NOT_FOUND)

        if senior.role != 'SENIOR':
            return Response({'detail': 'User is not a SENIOR.'}, status=status.HTTP_400_BAD_REQUEST)

        delta = request.data.get('delta', 1)
        try:
            delta = int(delta)
        except (TypeError, ValueError):
            return Response({'detail': 'delta must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        if delta < 0:
            return Response({'detail': 'delta must be non-negative.'}, status=status.HTTP_400_BAD_REQUEST)

        senior.active_load += delta
        senior.save()

        return Response(
            {
                'senior_id': str(senior.id),
                'active_load': senior.active_load,
            },
            status=status.HTTP_200_OK,
        )

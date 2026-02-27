from rest_framework.views import APIView
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.auth_service.models import Achievement, Senior, Student, User
from .models import UserProfile
from .serializers import AchievementSerializer, UpdateProfileSerializer, UserProfileResponseSerializer


def _authorized_for_user(request, target_user):
    return str(request.user.id) == str(target_user.id) or bool(getattr(request.user, 'is_staff', False))


def _build_profile_payload(user):
    student = getattr(user, 'student_profile', None)
    senior = getattr(user, 'senior_profile', None)
    achievements = Achievement.objects.filter(user=user).order_by('-created_at')

    achievement_data = [
        {
            'id': item.id,
            'title': item.title,
            'proof_url': item.proof_url,
            'verified': item.verified,
            'created_at': item.created_at,
        }
        for item in achievements
    ]

    payload = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'availability': user.availability,
        'trust_score': user.trust_score,
        'current_level': user.current_level,
        'active_load': user.active_load,
        'low_energy_mode': student.low_energy_mode if student else None,
        'momentum_score': student.momentum_score if student else None,
        'consistency_score': senior.consistency_score if senior else None,
        'alignment_score': senior.alignment_score if senior else None,
        'follow_through_rate': senior.follow_through_rate if senior else None,
        'achievements': achievement_data,
    }
    serializer = UserProfileResponseSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _is_internal_request(request):
    return request.headers.get('X-Internal-Secret') == settings.INTERNAL_SECRET


class UserProfileView(APIView):
    """
    GET  /api/profile/<user_id>/
    Output: UserProfileResponse
    Calls:  Nothing
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not _authorized_for_user(request, user):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        UserProfile.objects.get_or_create(user=user)
        return Response(_build_profile_payload(user), status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    """
    PUT /api/profile/<user_id>/update/
    Input:  Partial UserProfileResponse fields
    Output: Updated UserProfileResponse
    """
    permission_classes = [IsAuthenticated]

    def _update(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not _authorized_for_user(request, user):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UpdateProfileSerializer(data=request.data, partial=True, context={'role': user.role})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field in ['name', 'availability', 'current_level']:
            if field in data:
                setattr(user, field, data[field])

        try:
            user.save()
        except DjangoValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        if user.role == 'STUDENT':
            student, _ = Student.objects.get_or_create(user=user)
            for field in ['low_energy_mode', 'momentum_score']:
                if field in data:
                    setattr(student, field, data[field])
            student.save()

        if user.role == 'SENIOR':
            senior, _ = Senior.objects.get_or_create(user=user)
            for field in ['consistency_score', 'alignment_score', 'follow_through_rate']:
                if field in data:
                    setattr(senior, field, data[field])
            senior.save()

        UserProfile.objects.get_or_create(user=user)
        return Response(_build_profile_payload(user), status=status.HTTP_200_OK)

    def put(self, request, user_id):
        return self._update(request, user_id)

    def patch(self, request, user_id):
        return self._update(request, user_id)


class AchievementView(APIView):
    """
    POST /api/profile/<user_id>/achievements/
    Input:  { title, proof_url }
    Output: { id, title, proof_url, verified: false }
    Calls:  trust_score_service — POST /internal/trust-score/recalculate/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not _authorized_for_user(request, user):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        if user.role != 'SENIOR':
            return Response({'detail': 'Only SENIOR users can add achievements.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AchievementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        achievement = Achievement.objects.create(
            user=user,
            title=serializer.validated_data['title'],
            proof_url=serializer.validated_data.get('proof_url', ''),
        )

        output = AchievementSerializer(achievement)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not _authorized_for_user(request, user):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        achievements = Achievement.objects.filter(user=user).order_by('-created_at')
        data = AchievementSerializer(achievements, many=True).data
        return Response({'achievements': data}, status=status.HTTP_200_OK)


class InternalProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        if not _is_internal_request(request):
            return Response({'detail': 'Unauthorized internal request.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        UserProfile.objects.get_or_create(user=user)
        return Response(_build_profile_payload(user), status=status.HTTP_200_OK)

    def patch(self, request, user_id):
        if not _is_internal_request(request):
            return Response({'detail': 'Unauthorized internal request.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateProfileSerializer(data=request.data, partial=True, context={'role': user.role})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field in ['name', 'availability', 'current_level']:
            if field in data:
                setattr(user, field, data[field])
        user.save()

        if user.role == 'STUDENT':
            student, _ = Student.objects.get_or_create(user=user)
            for field in ['low_energy_mode', 'momentum_score']:
                if field in data:
                    setattr(student, field, data[field])
            student.save()

        if user.role == 'SENIOR':
            senior, _ = Senior.objects.get_or_create(user=user)
            for field in ['consistency_score', 'alignment_score', 'follow_through_rate']:
                if field in data:
                    setattr(senior, field, data[field])
            senior.save()

        UserProfile.objects.get_or_create(user=user)
        return Response(_build_profile_payload(user), status=status.HTTP_200_OK)

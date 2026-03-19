from rest_framework.views import APIView
from django.conf import settings
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import logging

from apps.auth_service.models import Achievement, Senior, Student, User
from .models import UserProfile
from .serializers import AchievementSerializer, UpdateProfileSerializer, UserProfileResponseSerializer

logger = logging.getLogger(__name__)
url_validator = URLValidator()


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

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'availability': user.availability,
        'trust_score': user.trust_score,
        'current_level': user.current_level,
        'active_load': user.active_load,
        'profile_completed': user.profile_completed,
        'low_energy_mode': student.low_energy_mode if student else None,
        'momentum_score': student.momentum_score if student else None,
        'consistency_score': senior.consistency_score if senior else None,
        'alignment_score': senior.alignment_score if senior else None,
        'follow_through_rate': senior.follow_through_rate if senior else None,
        'achievements': achievement_data,
    }


def _is_internal_request(request):
    return request.headers.get('X-Internal-Secret') == settings.INTERNAL_SECRET


class UserProfileView(APIView):
    """
    GET  /api/profile/<user_id>/
    Output: UserProfileResponse
    Calls:  Nothing
    Any authenticated user can view any profile (public info).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        UserProfile.objects.get_or_create(user=user)
        return Response(_build_profile_payload(user), status=status.HTTP_200_OK)


class UpdateProfileView(APIView):
    """
    PUT /api/profile/<user_id>/update/
    Input:  Partial UserProfileResponse fields
    Output: Updated UserProfileResponse
    """
    permission_classes = [IsAuthenticated]

    def _update(self, request, user_id, skip_auth=False):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not skip_auth and not _authorized_for_user(request, user):
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

        # ── Sync achievement to Neo4j as an EXPERIENCED_IN domain edge ──
        self._sync_achievement_to_graph(user, serializer.validated_data['title'])

        output = AchievementSerializer(achievement)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _sync_achievement_to_graph(user, title: str):
        """
        Treat the achievement title as a domain the senior is experienced in.
        Find or create the DomainNode, then ensure an EXPERIENCED_IN edge exists.
        """
        try:
            from apps.domain_management_service.graph_models import UserNode, DomainNode
            from apps.domain_management_service.views import find_existing_domain

            # Ensure UserNode exists
            try:
                user_node = UserNode.nodes.get(uid=str(user.id))
            except UserNode.DoesNotExist:
                user_node = UserNode(
                    uid=str(user.id),
                    role=user.role,
                    availability=user.availability,
                    trust_score=user.trust_score,
                    current_level=user.current_level,
                    active_load=user.active_load,
                    name=user.name,
                ).save()

            # Find or create domain node
            domain_node = find_existing_domain(title)
            if domain_node is None:
                domain_node = DomainNode(
                    name=title.strip().title(),
                    type='general',
                    popularity_score=1.0,
                ).save()
                logger.info('Created new domain from achievement: %s (uid=%s)', domain_node.name, domain_node.uid)
            else:
                domain_node.popularity_score = (domain_node.popularity_score or 0) + 1
                domain_node.save()

            # Create EXPERIENCED_IN edge if not already connected
            if not user_node.experienced_in.is_connected(domain_node):
                user_node.experienced_in.connect(domain_node, {
                    'experience_level': 'intermediate',
                    'years_of_involvement': 0,
                })
                logger.info('Created EXPERIENCED_IN edge: %s -> %s', user.name, domain_node.name)
        except Exception as exc:
            logger.warning('Failed to sync achievement to Neo4j graph: %s', exc)

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

        # Delegate to UpdateProfileView to avoid code duplication
        update_view = UpdateProfileView()
        update_view.request = request
        return update_view._update(request, user_id, skip_auth=True)


class SeniorOnboardingView(APIView):
    """
    POST /api/profile/<user_id>/onboarding/
    Mandatory senior profile completion after registration.
    Input: { current_level, domains: [str], achievements: [{title, proof_url?}] }
    - domains: at least 1 required
    - achievements: at least 1 required
    Creates domain links in Neo4j and achievements in DB,
    then sets user.profile_completed = True.
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
            return Response({'detail': 'Onboarding is only for SENIOR users.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.profile_completed:
            return Response({'detail': 'Profile already completed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate input
        current_level = (request.data.get('current_level') or '').strip()
        domains = request.data.get('domains', [])
        achievements = request.data.get('achievements', [])

        errors = {}
        if not current_level:
            errors['current_level'] = 'Current level is required.'
        if not domains or not isinstance(domains, list) or len(domains) == 0:
            errors['domains'] = 'At least one domain of expertise is required.'
        if not achievements or not isinstance(achievements, list) or len(achievements) == 0:
            errors['achievements'] = 'At least one achievement is required.'

        # Validate each achievement has a title and proof URL
        if isinstance(achievements, list):
            for i, ach in enumerate(achievements):
                if not isinstance(ach, dict) or not ach.get('title', '').strip():
                    errors[f'achievements[{i}]'] = 'Each achievement must have a title.'
                    continue

                proof_url = (ach.get('proof_url') or '').strip()
                if not proof_url:
                    errors[f'achievements[{i}].proof_url'] = 'Proof URL is required for each achievement.'
                    continue

                try:
                    url_validator(proof_url)
                except DjangoValidationError:
                    errors[f'achievements[{i}].proof_url'] = 'Enter a valid proof URL.'

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Update user basic info
        user.current_level = current_level
        user.save(update_fields=['current_level'])

        # Create achievements
        for ach in achievements:
            title = ach['title'].strip()
            proof_url = ach.get('proof_url', '').strip()
            Achievement.objects.create(user=user, title=title, proof_url=proof_url)
            # Sync to Neo4j graph
            AchievementView._sync_achievement_to_graph(user, title)

        # Add domains via the domain management service
        from apps.domain_management_service.views import AddDomainView
        domain_view = AddDomainView()
        added_domains = []
        for domain_text in domains:
            if not isinstance(domain_text, str) or not domain_text.strip():
                continue
            try:
                from rest_framework.test import APIRequestFactory
                factory = APIRequestFactory()
                fake_request = factory.post('/api/domains/add/', {
                    'user_id': str(user.id),
                    'raw_interest_text': domain_text.strip(),
                }, format='json')
                fake_request.user = request.user
                resp = domain_view.post(fake_request)
                if resp.status_code == 201:
                    added_domains.append(resp.data)
            except Exception as exc:
                logger.warning('Failed to add domain "%s" during onboarding: %s', domain_text, exc)

        # Mark profile as completed
        user.profile_completed = True
        user.save(update_fields=['profile_completed'])

        UserProfile.objects.get_or_create(user=user)
        return Response(_build_profile_payload(user), status=status.HTTP_200_OK)

import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.auth_service.models import User
from .matching_engine import MentorMatchingEngine
from .serializers import (
    MentorMatchRequestSerializer,
    MentorMatchResponseSerializer,
    PeerMatchResponseSerializer,
    ConnectMentorRequestSerializer,
    FindPeerRequestSerializer,
)

logger = logging.getLogger(__name__)


class FindMentorView(APIView):
    """
    POST /api/mentor-matching/find/
    Input:  MentorMatchRequest { student_id, domain_id, priority }
    Output: MentorMatchResponse
    Calls:  MentorMatchingEngine.find_mentors()
    """

    def post(self, request):
        serializer = MentorMatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        student_id = payload['student_id']
        domain_id = payload['domain_id']
        priority = payload.get('priority', 1)

        # Validate student exists
        if not User.objects.filter(id=student_id, role='STUDENT').exists():
            return Response(
                {'detail': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        engine = MentorMatchingEngine()
        mentors = engine.find_mentors(student_id, domain_id, priority)

        response_serializer = MentorMatchResponseSerializer(data=mentors, many=True)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ConnectMentorView(APIView):
    """
    POST /api/mentor-matching/connect/
    Input:  { student_id, senior_id, domain_id }
    Output: { mentorship_id, status }
    Calls:  MentorMatchingEngine.create_mentorship_edge()
    """

    def post(self, request):
        serializer = ConnectMentorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        student_id = payload['student_id']
        senior_id = payload['senior_id']
        domain_id = payload['domain_id']

        # Validate both users exist with correct roles
        if not User.objects.filter(id=student_id, role='STUDENT').exists():
            return Response(
                {'detail': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not User.objects.filter(id=senior_id, role='SENIOR').exists():
            return Response(
                {'detail': 'Senior not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        engine = MentorMatchingEngine()
        try:
            result = engine.create_mentorship_edge(student_id, senior_id, domain_id)
        except ValueError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result, status=status.HTTP_201_CREATED)


class FindPeerView(APIView):
    """
    POST /api/peer-matching/find/
    Input:  { student_id, domain_id }
    Output: PeerMatchResponse
    Calls:  MentorMatchingEngine.find_peers()
    """

    def post(self, request):
        serializer = FindPeerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        student_id = payload['student_id']
        domain_id = payload['domain_id']

        # Validate student exists
        if not User.objects.filter(id=student_id, role='STUDENT').exists():
            return Response(
                {'detail': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        engine = MentorMatchingEngine()
        peers = engine.find_peers(student_id, domain_id)

        response_serializer = PeerMatchResponseSerializer(data=peers, many=True)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# ──────────────────── Internal Views ────────────────────


class InternalFindMentorView(APIView):
    """
    POST /internal/mentor-matching/find/
    Internal endpoint used by query_orchestrator.
    """

    def post(self, request):
        view = FindMentorView()
        return view.post(request)


class InternalConnectMentorView(APIView):
    """
    POST /internal/mentor-matching/connect/
    Internal endpoint used by query_orchestrator.
    """

    def post(self, request):
        view = ConnectMentorView()
        return view.post(request)

from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.auth_service.models import User
from apps.query_orchestrator.models import Query
from .models import ChatRequest, DirectMessage
from .serializers import (
    InitiateChatRequestSerializer,
    ChatRequestResponseSerializer,
    RespondChatRequestSerializer,
    SendMessageSerializer,
    DirectMessageSerializer,
)
from .intro_generator import IntroMessageGenerator


class InitiateChatRequestView(APIView):
    """
    POST /api/dm/initiate/
    Student creates a ChatRequest to a senior from a resolved query.
    Auto-generates an intro message via LLM.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiateChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student_id = serializer.validated_data['student_id']
        senior_id = serializer.validated_data['senior_id']
        query_id = serializer.validated_data['query_id']

        # Fetch objects
        student = get_object_or_404(User, id=student_id, role='STUDENT')
        senior = get_object_or_404(User, id=senior_id, role='SENIOR')
        query = get_object_or_404(Query, id=query_id)

        # Validate query belongs to this student
        if str(query.student_id) != str(student_id):
            return Response(
                {'error': 'Query does not belong to the specified student.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate query is RESOLVED
        if not query.is_resolved and query.status != 'RESOLVED':
            return Response(
                {'error': 'Can only initiate DM after a query is resolved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate senior was one of the matched seniors on this query
        matched_senior_ids = [str(s) for s in query.matched_seniors] if query.matched_seniors else []
        if matched_senior_ids and str(senior_id) not in matched_senior_ids:
            return Response(
                {'error': 'The specified senior was not matched to this query.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for duplicate request
        if ChatRequest.objects.filter(student=student, senior=senior, query=query).exists():
            return Response(
                {'error': 'A chat request already exists for this student-senior-query combination.'},
                status=status.HTTP_409_CONFLICT,
            )

        # Generate intro message via LLM
        domain_name = str(query.domain_id)
        try:
            from apps.domain_management_service.views import _get_domain_name
            domain_name = _get_domain_name(query.domain_id) or domain_name
        except Exception:
            pass

        generator = IntroMessageGenerator()
        intro = generator.generate(student=student, query=query, domain_name=domain_name)

        # Create ChatRequest
        chat_request = ChatRequest.objects.create(
            student=student,
            senior=senior,
            query=query,
            intro_message=intro,
            status='PENDING',
        )

        return Response(
            ChatRequestResponseSerializer(chat_request).data,
            status=status.HTTP_201_CREATED,
        )


class RespondChatRequestView(APIView):
    """
    POST /api/dm/requests/<id>/respond/
    Senior accepts or rejects a pending chat request.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        chat_request = get_object_or_404(ChatRequest, id=pk)

        # Only the senior can respond
        if str(request.user.id) != str(chat_request.senior_id):
            return Response(
                {'error': 'Only the addressed senior can respond to this request.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if chat_request.status != 'PENDING':
            return Response(
                {'error': f'Chat request is already {chat_request.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RespondChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        action = serializer.validated_data['action']
        chat_request.status = 'ACCEPTED' if action == 'ACCEPT' else 'REJECTED'
        chat_request.responded_at = timezone.now()
        chat_request.save()

        return Response(ChatRequestResponseSerializer(chat_request).data)


class MessageListCreateView(APIView):
    """
    GET  /api/dm/requests/<id>/messages/  — list all messages in this thread
    POST /api/dm/requests/<id>/messages/  — send a message (only if ACCEPTED)
    """
    permission_classes = [IsAuthenticated]

    def _get_and_authorize(self, pk, user):
        """Return ChatRequest or raise 403/404."""
        chat_request = get_object_or_404(ChatRequest, id=pk)
        user_id = str(user.id)
        if user_id not in (str(chat_request.student_id), str(chat_request.senior_id)):
            return None, Response(
                {'error': 'You are not a participant in this chat.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return chat_request, None

    def get(self, request, pk):
        chat_request, err = self._get_and_authorize(pk, request.user)
        if err:
            return err

        messages = chat_request.messages.select_related('sender').all()
        return Response(DirectMessageSerializer(messages, many=True).data)

    def post(self, request, pk):
        chat_request, err = self._get_and_authorize(pk, request.user)
        if err:
            return err

        if chat_request.status != 'ACCEPTED':
            return Response(
                {'error': 'Cannot send messages until the chat request is accepted.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sender_id = serializer.validated_data['sender_id']
        content = serializer.validated_data['content']

        # Sender must be a participant
        if str(sender_id) not in (str(chat_request.student_id), str(chat_request.senior_id)):
            return Response(
                {'error': 'Sender is not a participant in this chat.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        sender = get_object_or_404(User, id=sender_id)
        message = DirectMessage.objects.create(
            chat_request=chat_request,
            sender=sender,
            content=content,
        )

        return Response(DirectMessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ChatRequestListView(APIView):
    """
    GET /api/dm/requests/
    Lists all chat requests for the authenticated user:
      - Senior: incoming requests (dm_requests_received)
      - Student: outgoing requests (dm_requests_sent)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'SENIOR':
            queryset = ChatRequest.objects.filter(senior=user).select_related('student', 'senior', 'query')
        else:
            queryset = ChatRequest.objects.filter(student=user).select_related('student', 'senior', 'query')

        return Response(ChatRequestResponseSerializer(queryset, many=True).data)

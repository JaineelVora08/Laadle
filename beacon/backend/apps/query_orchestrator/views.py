from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    QuerySubmitRequestSerializer,
    QuerySubmitResponseSerializer,
    SeniorResponseRequestSerializer,
    SeniorResponseStep1ResponseSerializer,
    SeniorFAQResponseRequestSerializer,
    FinalAdviceResponseSerializer,
    QueryStatusResponseSerializer,
    FollowUpRequestSerializer,
    FollowUpResponseSerializer,
)
from .orchestrator import QueryOrchestrator
from .models import Query, SeniorQueryAssignment


class SubmitQueryView(APIView):
    """
    POST /api/query/submit/
    Input:  QuerySubmitRequest { student_id, domain_id, content }
    Output: QuerySubmitResponse
    """
    def post(self, request):
        serializer = QuerySubmitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator = QueryOrchestrator()
        result = orchestrator.handle_new_query(
            student_id=str(serializer.validated_data['student_id']),
            domain_id=str(serializer.validated_data['domain_id']),
            content=serializer.validated_data['content']
        )

        response_serializer = QuerySubmitResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class QueryStatusView(APIView):
    """
    GET /api/query/<query_id>/status/
    Output: QueryStatusResponse
    """
    def get(self, request, query_id):
        try:
            query = Query.objects.get(id=query_id)
        except Query.DoesNotExist:
            return Response(
                {'error': 'Query not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        result = {
            'query_id': str(query.id),
            'status': query.status,
            'provisional_answer': query.rag_response or None,
            'final_answer': query.final_response or None,
            'follow_up_questions': query.follow_up_questions,
            'conflict_detected': query.conflicts.exists()
        }

        serializer = QueryStatusResponseSerializer(result)
        return Response(serializer.data)


class SeniorResponseView(APIView):
    """
    POST /api/query/<query_id>/senior-response/
    Step 1: Senior submits main advice.
    Output: Predicted FAQs for Step 2.
    """
    def post(self, request, query_id):
        serializer = SeniorResponseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator = QueryOrchestrator()
        result = orchestrator.handle_senior_response(
            senior_id=str(serializer.validated_data['senior_id']),
            query_id=str(query_id),
            advice_content=serializer.validated_data['advice_content']
        )

        response_serializer = SeniorResponseStep1ResponseSerializer(result)
        return Response(response_serializer.data)


class SeniorFAQResponseView(APIView):
    """
    POST /api/query/<query_id>/senior-faq/
    Step 2: Senior submits FAQ answers.
    Output: Final synthesized advice.
    """
    def post(self, request, query_id):
        serializer = SeniorFAQResponseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator = QueryOrchestrator()
        result = orchestrator.handle_senior_faq_response(
            senior_id=str(serializer.validated_data['senior_id']),
            query_id=str(query_id),
            faq_answers=serializer.validated_data['faq_answers']
        )

        response_serializer = FinalAdviceResponseSerializer(result)
        return Response(response_serializer.data)


class FollowUpView(APIView):
    """
    POST /api/query/<query_id>/followup/
    Student asks a follow-up question.
    Output: Instant reply, RAG provisional, or pending status.
    """
    def post(self, request, query_id):
        serializer = FollowUpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator = QueryOrchestrator()
        result = orchestrator.handle_followup_question(
            query_id=str(query_id),
            followup_text=serializer.validated_data['content']
        )

        response_serializer = FollowUpResponseSerializer(result)
        return Response(response_serializer.data)


class SeniorPendingQueriesView(APIView):
    """
    GET /api/query/pending/senior/<senior_id>/
    Output: list of pending QuerySubmitResponse objects
    """
    def get(self, request, senior_id):
        pending = SeniorQueryAssignment.objects.filter(
            senior_id=senior_id,
            status='PENDING'
        ).select_related('query')

        results = []
        for assignment in pending:
            q = assignment.query
            results.append({
                'query_id': str(q.id),
                'status': q.status,
                'provisional_answer': '',  # Senior doesn't see AI provisional answer
                'follow_up_questions': q.follow_up_questions,
                'matched_seniors': q.matched_seniors,
                'timestamp': q.timestamp.isoformat()
            })

        serializer = QuerySubmitResponseSerializer(results, many=True)
        return Response(serializer.data)

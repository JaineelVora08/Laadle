import logging

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
    StudentRatingRequestSerializer,
    FollowThroughRequestSerializer,
    FinalizeRequestSerializer,
    SeniorFAQStep2ResponseSerializer,
    ResponseStatusSerializer,
)
from .orchestrator import QueryOrchestrator
from .models import Query, SeniorQueryAssignment


logger = logging.getLogger(__name__)


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
            domain_ids=[str(d) for d in serializer.validated_data['domain_ids']],
            content=serializer.validated_data['content']
        )

        response_serializer = QuerySubmitResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class QueryStatusView(APIView):
    """
    GET /api/query/<query_id>/status/
    Output: QueryStatusResponse — includes full resolution data.
    """
    def get(self, request, query_id):
        try:
            query = Query.objects.get(id=query_id)
        except Query.DoesNotExist:
            return Response(
                {'error': 'Query not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Build contributing seniors from assignments
        contributing_seniors = []
        if query.status == 'RESOLVED':
            for a in query.assignments.filter(status='RESPONDED'):
                contributing_seniors.append({
                    'senior_id': str(a.senior_id),
                    'trust_score': float(a.trust_score_at_response or 0),
                    'weight': float(a.similarity_score or 0),
                })

        conflict = query.conflicts.first()
        cluster = query.cluster
        cluster_count = cluster.queries.count() if cluster else 0

        # Response status for majority mechanism
        total_assigned = query.assignments.count()
        total_responded = query.assignments.filter(status='RESPONDED').count()
        faq_completed_count = query.assignments.filter(faq_completed=True).count()

        from django.utils import timezone as tz
        now = tz.now()
        deadline = query.response_deadline
        deadline_passed = bool(deadline and now >= deadline)
        time_remaining = None
        if deadline and not deadline_passed:
            time_remaining = max(0, (deadline - now).total_seconds())

        can_finalize = (
            faq_completed_count >= 1
            and query.status != 'RESOLVED'
            and query.finalized_by is None
        )

        result = {
            'query_id': str(query.id),
            'content': query.content,
            'status': query.status,
            'is_resolved': query.is_resolved or query.status == 'RESOLVED',
            'provisional_answer': query.rag_response or None,
            'final_answer': query.final_response or None,
            'follow_up_questions': query.follow_up_questions,
            'conflict_detected': query.conflicts.exists(),
            'conflict_details': conflict.new_advice if conflict else None,
            'contributing_seniors': contributing_seniors,
            'student_rating': query.student_rating,
            'follow_through_success': query.follow_through_success,
            'follow_through_proof': query.follow_through_proof,
            'cluster_id': str(cluster.id) if cluster else None,
            'cluster_student_count': cluster_count,
            # Majority mechanism fields
            'total_assigned': total_assigned,
            'responses_received': total_responded,
            'faq_completed_count': faq_completed_count,
            'response_deadline': deadline.isoformat() if deadline else None,
            'deadline_passed': deadline_passed,
            'time_remaining_seconds': time_remaining,
            'can_finalize': can_finalize,
            'finalized_by': query.finalized_by,
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
    Output: Status of response recording (does NOT auto-resolve unless all seniors done).
    """
    def post(self, request, query_id):
        serializer = SeniorFAQResponseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator = QueryOrchestrator()
        try:
            result = orchestrator.handle_senior_faq_response(
                senior_id=str(serializer.validated_data['senior_id']),
                query_id=str(query_id),
                faq_answers=serializer.validated_data['faq_answers']
            )
        except Exception as exc:
            logger.exception('Failed to submit senior FAQ for query %s', query_id)
            return Response(
                {'detail': f'Failed to finalize FAQ response: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # If auto-finalized (all seniors responded), return full resolution
        if result.get('auto_finalized'):
            response_serializer = FinalAdviceResponseSerializer(result)
            return Response(response_serializer.data)

        # Otherwise return lightweight status
        response_serializer = SeniorFAQStep2ResponseSerializer(result)
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
            # For clustered queries show representative content + student count
            cluster = q.cluster
            display_content = (
                cluster.representative_content if cluster else q.content
            )
            cluster_count = cluster.queries.count() if cluster else 0
            results.append({
                'query_id': str(q.id),
                'content': display_content,
                'status': q.status,
                'provisional_answer': '',  # Senior doesn't see AI provisional answer
                'follow_up_questions': q.follow_up_questions,
                'matched_seniors': q.matched_seniors,
                'timestamp': q.timestamp.isoformat(),
                'cluster_id': str(cluster.id) if cluster else None,
                'cluster_student_count': cluster_count,
            })

        serializer = QuerySubmitResponseSerializer(results, many=True)
        return Response(serializer.data)


class StudentQueriesView(APIView):
    """
    GET /api/query/student/<student_id>/
    Returns all queries for a student with full resolution data.
    """
    def get(self, request, student_id):
        queries = Query.objects.filter(student_id=student_id).order_by('-timestamp')

        results = []
        for q in queries:
            # Build contributing seniors
            contributing_seniors = []
            if q.status == 'RESOLVED':
                for a in q.assignments.filter(status='RESPONDED'):
                    contributing_seniors.append({
                        'senior_id': str(a.senior_id),
                        'trust_score': float(a.trust_score_at_response or 0),
                        'weight': float(a.similarity_score or 0),
                    })

            conflict = q.conflicts.first()

            # Response status for majority mechanism
            total_assigned = q.assignments.count()
            total_responded = q.assignments.filter(status='RESPONDED').count()
            faq_completed_count = q.assignments.filter(faq_completed=True).count()

            from django.utils import timezone as tz
            now = tz.now()
            deadline = q.response_deadline
            deadline_passed = bool(deadline and now >= deadline)
            time_remaining = None
            if deadline and not deadline_passed:
                time_remaining = max(0, (deadline - now).total_seconds())

            can_finalize = (
                faq_completed_count >= 1
                and q.status != 'RESOLVED'
                and q.finalized_by is None
            )

            results.append({
                'query_id': str(q.id),
                'content': q.content,
                'domain_ids': q.domain_ids,
                'status': q.status,
                'is_resolved': q.is_resolved or q.status == 'RESOLVED',
                'provisional_answer': q.rag_response or '',
                'final_answer': q.final_response or None,
                'follow_up_questions': q.follow_up_questions,
                'matched_seniors': q.matched_seniors,
                'conflict_detected': q.conflicts.exists(),
                'conflict_details': conflict.new_advice if conflict else None,
                'contributing_seniors': contributing_seniors,
                'timestamp': q.timestamp.isoformat(),
                'student_rating': q.student_rating,
                'follow_through_success': q.follow_through_success,
                'follow_through_proof': q.follow_through_proof,
                # Majority mechanism fields
                'total_assigned': total_assigned,
                'responses_received': total_responded,
                'faq_completed_count': faq_completed_count,
                'response_deadline': deadline.isoformat() if deadline else None,
                'deadline_passed': deadline_passed,
                'time_remaining_seconds': time_remaining,
                'can_finalize': can_finalize,
                'finalized_by': q.finalized_by,
            })

        return Response(results)


class RateQueryView(APIView):
    """
    POST /api/query/<query_id>/rate/
    Student rates the resolved advice (1-5 stars).
    Updates student_feedback_score ONLY for majority-group seniors.
    """
    def post(self, request, query_id):
        serializer = StudentRatingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = Query.objects.get(id=query_id)
        except Query.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)

        if str(query.student_id) != str(serializer.validated_data['student_id']):
            return Response({'error': 'Only the query author can rate.'}, status=status.HTTP_403_FORBIDDEN)

        if not query.is_resolved and query.status != 'RESOLVED':
            return Response({'error': 'Query must be resolved before rating.'}, status=status.HTTP_400_BAD_REQUEST)

        if query.student_rating is not None:
            return Response({'error': 'Query already rated.'}, status=status.HTTP_400_BAD_REQUEST)

        rating = serializer.validated_data['rating']
        rating_score = rating * 20.0

        query.student_rating = rating
        query.save(update_fields=['student_rating'])

        # Update student_feedback_score only for responding seniors
        # The majority/minority alignment was already handled during finalization
        from apps.trust_score_service.calculator import TrustScoreCalculator
        trust_calc = TrustScoreCalculator()

        responded = SeniorQueryAssignment.objects.filter(query=query, status='RESPONDED')
        for assignment in responded:
            try:
                trust_calc.update_feedback(str(assignment.senior_id), {
                    'student_feedback_score': rating_score,
                })
            except Exception:
                pass

        return Response({'detail': 'Rating submitted.', 'rating': rating}, status=status.HTTP_200_OK)


class FollowThroughView(APIView):
    """
    POST /api/query/<query_id>/follow-through/
    Student reports whether the advice helped (success/failure) with optional proof.
    Updates follow_through_rate (n_success, n_total) for all responding seniors.
    """
    def post(self, request, query_id):
        serializer = FollowThroughRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = Query.objects.get(id=query_id)
        except Query.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)

        if str(query.student_id) != str(serializer.validated_data['student_id']):
            return Response({'error': 'Only the query author can submit follow-through.'}, status=status.HTTP_403_FORBIDDEN)

        if not query.is_resolved and query.status != 'RESOLVED':
            return Response({'error': 'Query must be resolved before follow-through.'}, status=status.HTTP_400_BAD_REQUEST)

        if query.follow_through_success is not None:
            return Response({'error': 'Follow-through already submitted.'}, status=status.HTTP_400_BAD_REQUEST)

        success = serializer.validated_data['success']
        proof_url = serializer.validated_data.get('proof_url', '')

        query.follow_through_success = success
        query.follow_through_proof = proof_url
        query.save(update_fields=['follow_through_success', 'follow_through_proof'])

        # Update n_success/n_total for each responding senior
        from apps.trust_score_service.calculator import TrustScoreCalculator
        from apps.auth_service.models import TrustMetrics
        trust_calc = TrustScoreCalculator()

        responded = SeniorQueryAssignment.objects.filter(query=query, status='RESPONDED')
        for assignment in responded:
            try:
                senior_id = str(assignment.senior_id)
                metrics = TrustMetrics.objects.get(senior_id=senior_id)
                new_n_total = metrics.n_total + 1
                new_n_success = metrics.n_success + (1 if success else 0)
                trust_calc.update_feedback(senior_id, {
                    'n_success': new_n_success,
                    'n_total': new_n_total,
                })
            except Exception:
                pass

        return Response({
            'detail': 'Follow-through recorded.',
            'success': success,
            'proof_url': proof_url,
        }, status=status.HTTP_200_OK)


class FinalizeQueryView(APIView):
    """
    POST /api/query/<query_id>/finalize/
    Student triggers early finalization using majority of responses received so far.
    Input: { student_id }
    Output: FinalAdviceResponse (majority-based synthesis)
    """
    def post(self, request, query_id):
        serializer = FinalizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            query = Query.objects.get(id=query_id)
        except Query.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)

        if str(query.student_id) != str(serializer.validated_data['student_id']):
            return Response(
                {'error': 'Only the query author can finalize.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if query.status == 'RESOLVED':
            return Response(
                {'error': 'Query already resolved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Must have at least 1 completed response
        has_responses = query.assignments.filter(status='RESPONDED').exists()
        if not has_responses:
            return Response(
                {'error': 'No senior responses yet. Cannot finalize.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        orchestrator = QueryOrchestrator()
        try:
            result = orchestrator.finalize_query(str(query_id), triggered_by='STUDENT')
        except Exception as exc:
            logger.exception('Failed to finalize query %s', query_id)
            return Response(
                {'detail': f'Finalization failed: {str(exc)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = FinalAdviceResponseSerializer(result)
        return Response(response_serializer.data)


class QueryResponseStatusView(APIView):
    """
    GET /api/query/<query_id>/response-status/
    Returns response counts, deadline info, and finalization eligibility.
    """
    def get(self, request, query_id):
        try:
            orchestrator = QueryOrchestrator()
            result = orchestrator.get_query_response_status(str(query_id))
        except Query.DoesNotExist:
            return Response({'error': 'Query not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ResponseStatusSerializer(result)
        return Response(serializer.data)


class CheckDeadlinesView(APIView):
    """
    POST /api/query/check-deadlines/
    Triggers deadline check for all expired queries.
    Can be called by a cron job or Celery beat.
    """
    def post(self, request):
        orchestrator = QueryOrchestrator()
        finalized_ids = orchestrator.check_and_finalize_expired_queries()
        return Response({
            'finalized_count': len(finalized_ids),
            'finalized_query_ids': finalized_ids,
        })

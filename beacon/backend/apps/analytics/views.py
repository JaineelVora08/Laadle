from datetime import timedelta

from django.db.models import Avg, Count, F
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import Event
from apps.query_orchestrator.models import ConflictRecord, Query, SeniorQueryAssignment


class PlatformAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        last_7d = now - timedelta(days=7)

        total = Query.objects.count()
        resolved = Query.objects.filter(is_resolved=True).count()
        avg_resolution = SeniorQueryAssignment.objects.filter(
            status='RESPONDED',
            responded_at__isnull=False,
        ).annotate(
            delta=F('responded_at') - F('assigned_at')
        ).aggregate(avg=Avg('delta'))

        domain_heatmap = Query.objects.filter(
            timestamp__gte=last_7d
        ).values('domain_ids').annotate(
            count=Count('id')
        ).order_by('-count')[:20]

        try:
            from celery import current_app
            active = current_app.control.inspect().active() or {}
            queue_size = sum(len(tasks) for tasks in active.values())
        except Exception:
            queue_size = 0

        llm_events = Event.objects.filter(
            event_type__startswith='LLM_CALL',
            timestamp__gte=last_7d,
        ).count()
        conflicts = ConflictRecord.objects.filter(flagged_at__gte=last_7d).count()

        return Response({
            'kpis': {
                'total_queries': total,
                'resolved': resolved,
                'resolution_rate': round(resolved / total * 100, 1) if total else 0,
                'avg_resolution_time': str(avg_resolution['avg']),
                'conflicts_7d': conflicts,
                'llm_calls_7d': llm_events,
                'celery_active_tasks': queue_size,
            },
            'domain_heatmap': list(domain_heatmap),
        })

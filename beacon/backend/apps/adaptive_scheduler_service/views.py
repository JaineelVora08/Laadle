from rest_framework.views import APIView


class SchedulerStatusView(APIView):
    """
    GET /api/scheduler/status/
    Output: { active_tasks, pending_redistributions }
    """
    def get(self, request):
        pass

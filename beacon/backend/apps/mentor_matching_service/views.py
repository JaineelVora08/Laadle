from rest_framework.views import APIView


class FindMentorView(APIView):
    """
    POST /api/mentor-matching/find/
    Input:  MentorMatchRequest { student_id, domain_id, priority }
    Output: MentorMatchResponse
    Calls:  MentorMatchingEngine.find_mentors()
    """
    def post(self, request):
        pass


class ConnectMentorView(APIView):
    """
    POST /api/mentor-matching/connect/
    Input:  { student_id, senior_id, domain_id }
    Output: { mentorship_id, status }
    Calls:  MentorMatchingEngine.create_mentorship_edge()
    """
    def post(self, request):
        pass


class FindPeerView(APIView):
    """
    POST /api/peer-matching/find/
    Input:  { student_id, domain_id }
    Output: PeerMatchResponse
    Calls:  MentorMatchingEngine.find_peers()
    """
    def post(self, request):
        pass

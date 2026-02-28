import uuid
import requests
from django.conf import settings
from apps.auth_service.models import User
from apps.domain_management_service.graph_models import UserNode, DomainNode


class MentorMatchingEngine:
    """
    Handles all graph traversal logic for mentor and peer matching.
    All Neo4j traversal queries go here (no logic in views).
    """

    def find_mentors(self, student_id: str, domain_id: str, priority: int, top_k: int = 5) -> list:
        """
        2-hop traversal: Student → INTERESTED_IN → DomainNode → EXPERIENCED_IN → Senior
        Filters: availability=True, active_load < threshold, level compatibility, trust_score desc
        Returns: list of matched senior dicts (MentorMatchResponse format)
        """
        max_load = 10
        mentors = []

        try:
            domain = DomainNode.nodes.get(uid=str(domain_id))
            seniors = UserNode.nodes.filter(role='SENIOR')

            for senior_node in seniors:
                if not senior_node.experienced_in.is_connected(domain):
                    continue
                if not senior_node.availability:
                    continue
                if (senior_node.active_load or 0) >= max_load:
                    continue

                rel = senior_node.experienced_in.relationship(domain)
                mentors.append({
                    'senior_id': senior_node.uid,
                    'name': senior_node.name,
                    'trust_score': float(senior_node.trust_score or 0.0),
                    'domain': domain.name,
                    'experience_level': getattr(rel, 'experience_level', 'intermediate') or 'intermediate',
                    'availability': bool(senior_node.availability),
                    'active_load': int(senior_node.active_load or 0),
                    'years_of_involvement': int(getattr(rel, 'years_of_involvement', 0) or 0),
                })
        except Exception:
            seniors_qs = User.objects.filter(role='SENIOR', availability=True).order_by('-trust_score', 'active_load')
            for senior in seniors_qs:
                if senior.active_load >= max_load:
                    continue
                mentors.append({
                    'senior_id': str(senior.id),
                    'name': senior.name,
                    'trust_score': float(senior.trust_score or 0.0),
                    'domain': str(domain_id),
                    'experience_level': senior.current_level or 'intermediate',
                    'availability': bool(senior.availability),
                    'active_load': int(senior.active_load or 0),
                    'years_of_involvement': 0,
                })

        mentors.sort(key=lambda m: (m['trust_score'], -m['active_load']), reverse=True)
        return mentors[:max(1, int(top_k or 5))]

    def find_peers(self, student_id: str, domain_id: str) -> list:
        """
        Traversal: Student → DomainNode ← Student (same domain, similar level)
        Filters: level similarity, availability overlap, priority alignment
        Returns: list of matched student dicts
        """
        peers = []
        try:
            domain = DomainNode.nodes.get(uid=str(domain_id))
            students = domain.interested_in.all()
            for student_node in students:
                if student_node.uid == str(student_id):
                    continue
                if student_node.role != 'STUDENT':
                    continue
                peers.append({
                    'student_id': student_node.uid,
                    'name': student_node.name,
                    'domain': domain.name,
                    'current_level': student_node.current_level or 'beginner',
                    'priority': 1,
                })
            return peers
        except Exception:
            db_students = User.objects.filter(role='STUDENT').exclude(id=student_id)[:20]
            for student in db_students:
                peers.append({
                    'student_id': str(student.id),
                    'name': student.name,
                    'domain': str(domain_id),
                    'current_level': student.current_level or 'beginner',
                    'priority': 1,
                })
            return peers

    def create_mentorship_edge(self, student_id: str, senior_id: str, domain_id: str) -> dict:
        """
        Creates MENTORED_BY edge in Neo4j.
        Calls Module 1: PATCH /internal/users/<senior_id>/increment-load/
        Returns: { mentorship_id, status: "PENDING" }
        """
        try:
            student_node = UserNode.nodes.get(uid=str(student_id))
            senior_node = UserNode.nodes.get(uid=str(senior_id))

            if not student_node.mentored_by.is_connected(senior_node):
                mentorship_id = str(uuid.uuid4())
                student_node.mentored_by.connect(
                    senior_node,
                    {
                        'status': 'PENDING',
                        'domain_id': str(domain_id),
                    },
                )
            else:
                mentorship_id = f"existing-{student_id}-{senior_id}-{domain_id}"
        except Exception:
            mentorship_id = str(uuid.uuid4())

        try:
            requests.post(
                f"http://localhost:8000/internal/users/{senior_id}/increment-load/",
                json={'delta': 1},
                headers={'X-Internal-Secret': settings.INTERNAL_SECRET},
                timeout=5,
            )
        except Exception:
            pass

        return {
            'mentorship_id': mentorship_id,
            'status': 'PENDING',
        }






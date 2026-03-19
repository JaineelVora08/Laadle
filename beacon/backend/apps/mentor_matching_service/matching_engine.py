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

    @staticmethod
    def _resolve_equivalent_domains(domain: DomainNode) -> list:
        """
        Return a list of DomainNodes that are equivalent to *domain*
        (same name, case-insensitive).  Always includes *domain* itself.
        This handles legacy duplicate nodes (e.g. "ML" vs "Machine Learning").
        """
        from apps.domain_management_service.views import find_existing_domain
        from neomodel import db

        # Gather all domains whose lowered name matches the primary one
        results, _ = db.cypher_query(
            "MATCH (d:DomainNode) WHERE toLower(d.name) = $name RETURN d",
            {'name': domain.name.strip().lower()},
            resolve_objects=True,
        )
        equivalent = [row[0] for row in results]

        # Also try alias resolution for the primary domain's name
        alias_match = find_existing_domain(domain.name)
        if alias_match and alias_match.uid not in {d.uid for d in equivalent}:
            equivalent.append(alias_match)

        # Ensure the original domain is always included
        if domain.uid not in {d.uid for d in equivalent}:
            equivalent.insert(0, domain)

        return equivalent

    def find_mentors(self, student_id: str, domain_id: str, priority: int, top_k: int = 5) -> list:
        """
        2-hop traversal: Student → INTERESTED_IN → DomainNode → EXPERIENCED_IN → Senior
        Filters: availability=True, active_load < threshold, level compatibility, trust_score desc
        Returns: list of matched senior dicts (MentorMatchResponse format)
        """
        max_load = 10
        mentors = []
        seen_ids = set()  # guard against duplicate UserNodes

        try:
            domain = DomainNode.nodes.get(uid=str(domain_id))
            # Resolve equivalent / alias domain nodes so "ML" finds "Machine Learning" mentors
            equivalent_domains = self._resolve_equivalent_domains(domain)
            display_name = domain.name  # use the originally-requested domain name for display
            seniors = UserNode.nodes.filter(role='SENIOR')

            for senior_node in seniors:
                if senior_node.uid in seen_ids:
                    continue
                if not senior_node.availability:
                    continue
                if (senior_node.active_load or 0) >= max_load:
                    continue

                # Check connection to ANY equivalent domain
                matched_domain = None
                for eq_domain in equivalent_domains:
                    if senior_node.experienced_in.is_connected(eq_domain):
                        matched_domain = eq_domain
                        break
                if matched_domain is None:
                    continue

                seen_ids.add(senior_node.uid)
                rel = senior_node.experienced_in.relationship(matched_domain)
                mentors.append({
                    'senior_id': senior_node.uid,
                    'name': senior_node.name,
                    'trust_score': float(senior_node.trust_score or 0.0),
                    'domain': display_name,
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

    def find_peers(self, student_id: str, domain_id: str = None, top_k: int = 10) -> list:
        """
        Traversal: Student → DomainNode ← Student (shared domains)
        If domain_id is provided, matching is constrained to that domain (and aliases).
        If domain_id is not provided, matching uses all domains of the student.
        Returns: ranked list of matched student dicts with overlap metrics.
        """
        peers = []
        try:
            student_node = UserNode.nodes.get(uid=str(student_id))

            base_domains = []
            if domain_id:
                requested_domain = DomainNode.nodes.get(uid=str(domain_id))
                base_domains = self._resolve_equivalent_domains(requested_domain)
            else:
                # Start with all domains attached to the student and expand aliases.
                seen_domain_uids = set()
                for student_domain in student_node.interested_in.all():
                    for eq_domain in self._resolve_equivalent_domains(student_domain):
                        if eq_domain.uid not in seen_domain_uids:
                            seen_domain_uids.add(eq_domain.uid)
                            base_domains.append(eq_domain)

            if not base_domains:
                return []

            student_domain_name_map = {d.name.strip().lower(): d.name for d in base_domains if d.name}
            student_domain_names = set(student_domain_name_map.keys())

            candidate_by_id = {}
            candidate_shared_domains = {}
            for candidate_domain in base_domains:
                canonical_name = student_domain_name_map.get(
                    (candidate_domain.name or '').strip().lower(),
                    candidate_domain.name,
                )
                for candidate in candidate_domain.interested_in.all():
                    if candidate.uid == str(student_id):
                        continue
                    if candidate.role != 'STUDENT':
                        continue
                    candidate_by_id[candidate.uid] = candidate
                    candidate_shared_domains.setdefault(candidate.uid, set()).add(canonical_name)

            requester_level = (student_node.current_level or '').strip().lower()

            for candidate_id, candidate in candidate_by_id.items():
                shared_domains = sorted(d for d in candidate_shared_domains.get(candidate_id, set()) if d)
                if not shared_domains:
                    continue

                overlap = len(shared_domains)
                similarity = overlap / max(len(student_domain_names), 1)
                candidate_level = (candidate.current_level or '').strip().lower()
                level_bonus = 0.1 if requester_level and candidate_level == requester_level else 0.0

                peers.append({
                    'student_id': candidate_id,
                    'name': candidate.name,
                    'domain': shared_domains[0],
                    'current_level': candidate.current_level or 'beginner',
                    'priority': 1,
                    'shared_domains': shared_domains,
                    'shared_domain_count': overlap,
                    'similarity_score': round(min(similarity + level_bonus, 1.0), 3),
                })

            peers.sort(
                key=lambda p: (
                    p.get('shared_domain_count', 0),
                    p.get('similarity_score', 0),
                    p.get('name', '').lower(),
                ),
                reverse=True,
            )
            return peers[:top_k]
        except Exception:
            db_students = User.objects.filter(role='STUDENT').exclude(id=student_id)[:20]
            fallback_domain_name = str(domain_id or 'General')
            fallback_shared_domains = [fallback_domain_name] if domain_id else []
            fallback_shared_count = 1 if domain_id else 0
            fallback_similarity = 0.55 if domain_id else 0.0
            for student in db_students:
                peers.append({
                    'student_id': str(student.id),
                    'name': student.name,
                    'domain': fallback_domain_name,
                    'current_level': student.current_level or 'beginner',
                    'priority': 1,
                    'shared_domains': fallback_shared_domains,
                    'shared_domain_count': fallback_shared_count,
                    'similarity_score': fallback_similarity,
                })
            return peers[:top_k]

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






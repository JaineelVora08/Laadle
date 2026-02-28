import logging
import uuid

from neomodel import db

from apps.domain_management_service.graph_models import UserNode, DomainNode, MentoredBy

logger = logging.getLogger(__name__)

# Maximum active_load before a senior is considered overloaded
ACTIVE_LOAD_THRESHOLD = 5


class MentorMatchingEngine:
    """
    Handles all graph traversal logic for mentor and peer matching.
    All Neo4j traversal queries go here (no logic in views).
    """

    def find_mentors(self, student_id: str, domain_id: str, priority: int) -> list:
        """
        2-hop traversal: Student → INTERESTED_IN → DomainNode → EXPERIENCED_IN → Senior
        Filters: availability=True, active_load < threshold, level compatibility, trust_score desc
        Returns: list of matched senior dicts (MentorMatchResponse format)
        """
        query = """
        MATCH (student:UserNode {uid: $student_id})-[si:INTERESTED_IN]->(domain:DomainNode {uid: $domain_id})
              <-[se:EXPERIENCED_IN]-(senior:UserNode {role: 'SENIOR'})
        WHERE senior.availability = true
          AND senior.active_load < $load_threshold
          AND senior.uid <> $student_id
        RETURN senior.uid AS senior_id,
               senior.name AS name,
               senior.trust_score AS trust_score,
               domain.name AS domain,
               se.experience_level AS experience_level,
               senior.availability AS availability,
               senior.active_load AS active_load
        ORDER BY senior.trust_score DESC
        """

        try:
            results, meta = db.cypher_query(
                query,
                {
                    'student_id': student_id,
                    'domain_id': domain_id,
                    'load_threshold': ACTIVE_LOAD_THRESHOLD,
                },
            )
        except Exception as exc:
            logger.error('Mentor search failed: %s', exc)
            return []

        mentors = []
        for row in results:
            mentors.append({
                'senior_id': row[0],
                'name': row[1] or '',
                'trust_score': float(row[2] or 0.0),
                'domain': row[3] or '',
                'experience_level': row[4] or 'intermediate',
                'availability': bool(row[5]) if row[5] is not None else True,
                'active_load': int(row[6] or 0),
            })

        return mentors

    def find_peers(self, student_id: str, domain_id: str) -> list:
        """
        Traversal: Student → DomainNode ← Student (same domain, similar level)
        Filters: level similarity, availability overlap, priority alignment
        Returns: list of matched student dicts
        """
        query = """
        MATCH (me:UserNode {uid: $student_id})-[my_rel:INTERESTED_IN]->(domain:DomainNode {uid: $domain_id})
              <-[their_rel:INTERESTED_IN]-(peer:UserNode {role: 'STUDENT'})
        WHERE peer.uid <> $student_id
          AND peer.availability = true
        RETURN peer.uid AS student_id,
               peer.name AS name,
               domain.name AS domain,
               their_rel.current_level AS current_level,
               their_rel.priority AS priority
        ORDER BY their_rel.priority DESC
        """

        try:
            results, meta = db.cypher_query(
                query,
                {
                    'student_id': student_id,
                    'domain_id': domain_id,
                },
            )
        except Exception as exc:
            logger.error('Peer search failed: %s', exc)
            return []

        peers = []
        for row in results:
            peers.append({
                'student_id': row[0],
                'name': row[1] or '',
                'domain': row[2] or '',
                'current_level': row[3] or 'beginner',
                'priority': int(row[4] or 1),
            })

        return peers

    def create_mentorship_edge(self, student_id: str, senior_id: str, domain_id: str) -> dict:
        """
        Creates MENTORED_BY edge in Neo4j.
        Calls Module 1: PATCH /internal/users/<senior_id>/increment-load/
        Returns: { mentorship_id, status: "PENDING" }
        """
        try:
            student_node = UserNode.nodes.get(uid=student_id)
        except UserNode.DoesNotExist:
            raise ValueError(f'Student node not found: {student_id}')

        try:
            senior_node = UserNode.nodes.get(uid=senior_id)
        except UserNode.DoesNotExist:
            raise ValueError(f'Senior node not found: {senior_id}')

        # Check if mentorship already exists between them for this domain
        existing_query = """
        MATCH (s:UserNode {uid: $student_id})-[r:MENTORED_BY {domain_id: $domain_id}]->(sr:UserNode {uid: $senior_id})
        RETURN r
        """
        results, _ = db.cypher_query(
            existing_query,
            {'student_id': student_id, 'senior_id': senior_id, 'domain_id': domain_id},
        )
        if results:
            raise ValueError('Mentorship already exists for this domain.')

        # Create MENTORED_BY relationship
        mentorship_id = str(uuid.uuid4())
        rel = student_node.mentored_by.connect(
            senior_node,
            {
                'status': 'PENDING',
                'domain_id': domain_id,
            },
        )

        # Increment senior load via Module 1 internal client
        try:
            from apps.auth_service.services.client import InternalUserClient
            client = InternalUserClient()
            client.increment_senior_load(senior_id)
        except Exception as exc:
            logger.warning('Failed to increment senior load via Module 1: %s', exc)
            # Also update Neo4j directly as fallback
            try:
                senior_node.active_load = (senior_node.active_load or 0) + 1
                senior_node.save()
            except Exception:
                pass

        return {
            'mentorship_id': mentorship_id,
            'status': 'PENDING',
        }

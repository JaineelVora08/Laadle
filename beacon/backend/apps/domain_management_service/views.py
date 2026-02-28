import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.auth_service.models import User
from .graph_models import UserNode, DomainNode, InterestedIn, ExperiencedIn
from .serializers import (
    AddDomainRequestSerializer,
    DomainLinkResponseSerializer,
    DomainNodeSerializer,
)

logger = logging.getLogger(__name__)

# Cosine similarity threshold for domain deduplication
SIMILARITY_THRESHOLD = 0.85


class AddDomainView(APIView):
    """
    POST /api/domains/add/
    Input:  { user_id, raw_interest_text }
    Output: DomainLinkResponse
    Calls:  ai_services — POST /internal/embeddings/generate/
            Neo4j — cosine similarity check, create/link DomainNode
    """

    def post(self, request):
        serializer = AddDomainRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        user_id = payload['user_id']
        raw_text = payload['raw_interest_text']
        priority = payload.get('priority', 1)
        current_level = payload.get('current_level', 'beginner')
        experience_level = payload.get('experience_level', 'intermediate')
        years_of_involvement = payload.get('years_of_involvement', 0)

        # ── 1. Validate user exists in PostgreSQL ──
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── 2–6. Neo4j graph operations ──
        try:
            user_node = self._ensure_user_node(user)

            # ── 3. Generate embedding via ai_services ──
            embedding = self._generate_embedding(raw_text)

            # ── 4. Search for similar existing domains ──
            domain_node = None
            if embedding:
                similar = self._query_similar_domains(embedding)
                if similar:
                    best_match = similar[0]
                    if best_match['score'] >= SIMILARITY_THRESHOLD:
                        # Reuse existing domain
                        try:
                            domain_node = DomainNode.nodes.get(uid=best_match['metadata'].get('domain_id', ''))
                            # Increment popularity
                            domain_node.popularity_score = (domain_node.popularity_score or 0) + 1
                            domain_node.save()
                        except DomainNode.DoesNotExist:
                            domain_node = None

            # ── 5. Create new DomainNode if no match found ──
            if domain_node is None:
                domain_node = DomainNode(
                    name=raw_text.strip().title(),
                    type=self._infer_domain_type(raw_text),
                    popularity_score=1.0,
                ).save()

                # Store embedding in Pinecone
                if embedding:
                    self._store_embedding(
                        vector_id=domain_node.uid,
                        embedding=embedding,
                        metadata={
                            'domain_name': domain_node.name,
                            'type': domain_node.type,
                            'domain_id': domain_node.uid,
                        },
                    )
                    domain_node.embedding_ref = domain_node.uid
                    domain_node.save()

            # ── 6. Create relationship edge based on role ──
            if user.role == 'STUDENT':
                if not user_node.interested_in.is_connected(domain_node):
                    user_node.interested_in.connect(
                        domain_node,
                        {'priority': priority, 'current_level': current_level},
                    )
                else:
                    # Update existing relationship properties
                    rel = user_node.interested_in.relationship(domain_node)
                    rel.priority = priority
                    rel.current_level = current_level
                    rel.save()
            elif user.role == 'SENIOR':
                if not user_node.experienced_in.is_connected(domain_node):
                    user_node.experienced_in.connect(
                        domain_node,
                        {'experience_level': experience_level, 'years_of_involvement': years_of_involvement},
                    )
                else:
                    rel = user_node.experienced_in.relationship(domain_node)
                    rel.experience_level = experience_level
                    rel.years_of_involvement = years_of_involvement
                    rel.save()

        except Exception as neo4j_exc:
            logger.error('Neo4j operation failed in AddDomainView: %s', neo4j_exc)
            return Response(
                {
                    'detail': 'Graph database is unavailable. Please ensure Neo4j is running and try again.',
                    'error': str(neo4j_exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # ── 7. Build and return response ──
        response_data = {
            'domain_id': domain_node.uid,
            'name': domain_node.name,
            'type': domain_node.type,
            'priority': priority,
            'current_level': current_level,
            'embedding_ref': domain_node.embedding_ref or '',
            'popularity_score': domain_node.popularity_score or 0.0,
        }
        response_serializer = DomainLinkResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _ensure_user_node(user: User) -> UserNode:
        """Ensure user has a corresponding Neo4j node. Create if missing."""
        try:
            return UserNode.nodes.get(uid=str(user.id))
        except UserNode.DoesNotExist:
            return UserNode(
                uid=str(user.id),
                role=user.role,
                availability=user.availability,
                trust_score=user.trust_score,
                current_level=user.current_level,
                active_load=user.active_load,
                name=user.name,
            ).save()

    @staticmethod
    def _generate_embedding(text: str) -> list:
        """Call EmbeddingGenerator. Returns empty list on failure."""
        try:
            from apps.ai_services.embedding_generator import EmbeddingGenerator
            generator = EmbeddingGenerator()
            return generator.generate(text)
        except Exception as exc:
            logger.warning('Embedding generation failed: %s', exc)
            return []

    @staticmethod
    def _query_similar_domains(embedding: list) -> list:
        """Query Pinecone for similar domain embeddings."""
        try:
            from apps.ai_services.embedding_generator import EmbeddingGenerator
            generator = EmbeddingGenerator()
            return generator.query_similar(embedding, top_k=5)
        except Exception as exc:
            logger.warning('Similar domain query failed: %s', exc)
            return []

    @staticmethod
    def _store_embedding(vector_id: str, embedding: list, metadata: dict) -> bool:
        """Store embedding in Pinecone."""
        try:
            from apps.ai_services.embedding_generator import EmbeddingGenerator
            generator = EmbeddingGenerator()
            return generator.store(vector_id, embedding, metadata)
        except Exception as exc:
            logger.warning('Embedding storage failed: %s', exc)
            return False

    @staticmethod
    def _infer_domain_type(text: str) -> str:
        """Simple heuristic to infer domain type from text."""
        text_lower = text.lower()
        academic_keywords = {'math', 'science', 'physics', 'chemistry', 'biology', 'engineering',
                             'computer', 'programming', 'algorithm', 'data', 'machine learning',
                             'ai', 'artificial intelligence', 'statistics', 'calculus'}
        professional_keywords = {'business', 'management', 'marketing', 'finance', 'consulting',
                                 'leadership', 'entrepreneurship', 'startup', 'product'}
        creative_keywords = {'design', 'art', 'music', 'writing', 'photography', 'film',
                             'animation', 'creative', 'graphic'}

        for keyword in academic_keywords:
            if keyword in text_lower:
                return 'academic'
        for keyword in professional_keywords:
            if keyword in text_lower:
                return 'professional'
        for keyword in creative_keywords:
            if keyword in text_lower:
                return 'creative'
        return 'general'


class UserDomainsView(APIView):
    """
    GET /api/domains/user/<user_id>/
    Output: list of DomainLinkResponse
    """

    def get(self, request, user_id):
        # Validate user exists
        if not User.objects.filter(id=user_id).exists():
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            user_node = UserNode.nodes.get(uid=str(user_id))
        except UserNode.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        except Exception as neo4j_exc:
            logger.warning('Neo4j unavailable in UserDomainsView.get: %s', neo4j_exc)
            return Response([], status=status.HTTP_200_OK)

        domains = []
        user = User.objects.get(id=user_id)

        if user.role == 'STUDENT':
            for domain in user_node.interested_in.all():
                rel = user_node.interested_in.relationship(domain)
                domains.append({
                    'domain_id': domain.uid,
                    'name': domain.name,
                    'type': domain.type,
                    'priority': rel.priority,
                    'current_level': rel.current_level,
                    'embedding_ref': domain.embedding_ref or '',
                    'popularity_score': domain.popularity_score or 0.0,
                })
        elif user.role == 'SENIOR':
            for domain in user_node.experienced_in.all():
                rel = user_node.experienced_in.relationship(domain)
                domains.append({
                    'domain_id': domain.uid,
                    'name': domain.name,
                    'type': domain.type,
                    'priority': 0,  # Seniors don't have priority
                    'current_level': rel.experience_level,
                    'embedding_ref': domain.embedding_ref or '',
                    'popularity_score': domain.popularity_score or 0.0,
                })

        serializer = DomainLinkResponseSerializer(data=domains, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AllDomainsView(APIView):
    """
    GET /api/domains/all/
    Output: list of all DomainNode records
    """

    def get(self, request):
        try:
            all_domains = DomainNode.nodes.all()
        except Exception as neo4j_exc:
            logger.warning('Neo4j unavailable in AllDomainsView.get: %s', neo4j_exc)
            return Response([], status=status.HTTP_200_OK)

        data = [
            {
                'uid': d.uid,
                'name': d.name,
                'type': d.type,
                'embedding_ref': d.embedding_ref or '',
                'popularity_score': d.popularity_score or 0.0,
            }
            for d in all_domains
        ]
        serializer = DomainNodeSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ──────────────────── Internal Views ────────────────────


class InternalUserDomainsView(APIView):
    """
    GET /internal/domains/user/<user_id>/
    Returns: list of DomainLinkResponse dicts
    Used by other modules internally.
    """

    def get(self, request, user_id):
        # Reuse public view logic
        view = UserDomainsView()
        return view.get(request, user_id)


class InternalDomainDetailView(APIView):
    """
    GET /internal/domains/<domain_id>/
    Returns: DomainNode dict
    Used by other modules internally.
    """

    def get(self, request, domain_id):
        try:
            domain = DomainNode.nodes.get(uid=str(domain_id))
        except DomainNode.DoesNotExist:
            return Response(
                {'detail': 'Domain not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as neo4j_exc:
            logger.warning('Neo4j unavailable in InternalDomainDetailView.get: %s', neo4j_exc)
            return Response(
                {'detail': 'Graph database unavailable.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        data = {
            'uid': domain.uid,
            'name': domain.name,
            'type': domain.type,
            'embedding_ref': domain.embedding_ref or '',
            'popularity_score': domain.popularity_score or 0.0,
        }
        serializer = DomainNodeSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

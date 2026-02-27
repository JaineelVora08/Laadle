from neomodel import StructuredNode, StructuredRel


class UserNode(StructuredNode):
    """
    Neo4j node mirroring PostgreSQL User.
    Properties: uid, role, availability, trust_score, current_level, active_load
    """
    pass


class DomainNode(StructuredNode):
    """
    Neo4j node representing a domain/area of interest.
    Properties: uid, name, type, embedding_ref (Pinecone ID), popularity_score
    """
    pass


class InterestedIn(StructuredRel):
    """
    Relationship: Student → DomainNode
    Properties: priority (int), current_level (str)
    """
    pass


class ExperiencedIn(StructuredRel):
    """
    Relationship: Senior → DomainNode
    Properties: experience_level (str), years_of_involvement (int)
    """
    pass


class MentoredBy(StructuredRel):
    """
    Relationship: Student → Senior
    Properties: start_date, status (ACTIVE | CLOSED)
    """
    pass


class ConnectedWith(StructuredRel):
    """
    Peer relationship: Student ↔ Student
    Properties: since (date)
    """
    pass

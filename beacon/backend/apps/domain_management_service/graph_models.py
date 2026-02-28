import uuid

from neomodel import (
    StructuredNode,
    StructuredRel,
    StringProperty,
    FloatProperty,
    IntegerProperty,
    BooleanProperty,
    DateProperty,
    UniqueIdProperty,
    RelationshipTo,
    RelationshipFrom,
)


# ──────────────────────────── Relationship Models ────────────────────────────


class InterestedIn(StructuredRel):
    """
    Relationship: Student → DomainNode
    Properties: priority (int), current_level (str)
    """
    priority = IntegerProperty(default=1)
    current_level = StringProperty(default='beginner')


class ExperiencedIn(StructuredRel):
    """
    Relationship: Senior → DomainNode
    Properties: experience_level (str), years_of_involvement (int)
    """
    experience_level = StringProperty(default='intermediate')
    years_of_involvement = IntegerProperty(default=0)


class MentoredBy(StructuredRel):
    """
    Relationship: Student → Senior
    Properties: start_date, status (ACTIVE | CLOSED), domain_id
    """
    start_date = DateProperty(default_now=True)
    status = StringProperty(default='PENDING', choices={'PENDING': 'Pending', 'ACTIVE': 'Active', 'CLOSED': 'Closed'})
    domain_id = StringProperty()


class ConnectedWith(StructuredRel):
    """
    Peer relationship: Student ↔ Student
    Properties: since (date)
    """
    since = DateProperty(default_now=True)


# ──────────────────────────── Node Models ────────────────────────────────────


class DomainNode(StructuredNode):
    """
    Neo4j node representing a domain/area of interest.
    Properties: uid, name, type, embedding_ref (Pinecone ID), popularity_score
    """
    uid = UniqueIdProperty()
    name = StringProperty(required=True, index=True)
    type = StringProperty(default='general')
    embedding_ref = StringProperty(default='')
    popularity_score = FloatProperty(default=0.0)

    # Reverse relationships are defined on UserNode
    class Meta:
        app_label = 'domain_management_service'


class UserNode(StructuredNode):
    """
    Neo4j node mirroring PostgreSQL User.
    Properties: uid, role, availability, trust_score, current_level, active_load
    """
    uid = StringProperty(unique_index=True, required=True)
    role = StringProperty(required=True, choices={'STUDENT': 'Student', 'SENIOR': 'Senior'})
    availability = BooleanProperty(default=True)
    trust_score = FloatProperty(default=0.0)
    current_level = StringProperty(default='')
    active_load = IntegerProperty(default=0)
    name = StringProperty(default='')

    # Student relationships
    interested_in = RelationshipTo(DomainNode, 'INTERESTED_IN', model=InterestedIn)
    mentored_by = RelationshipTo('UserNode', 'MENTORED_BY', model=MentoredBy)
    connected_with = RelationshipTo('UserNode', 'CONNECTED_WITH', model=ConnectedWith)

    # Senior relationships
    experienced_in = RelationshipTo(DomainNode, 'EXPERIENCED_IN', model=ExperiencedIn)
    mentors = RelationshipFrom('UserNode', 'MENTORED_BY', model=MentoredBy)

    class Meta:
        app_label = 'domain_management_service'

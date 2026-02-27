from rest_framework import serializers


class DomainLinkResponseSerializer(serializers.Serializer):
    """Serializes DomainLinkResponse: domain_id, name, type, priority, current_level."""
    pass


class DomainNodeSerializer(serializers.Serializer):
    """Serializes DomainNode: uid, name, type, embedding_ref, popularity_score."""
    pass

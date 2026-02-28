from rest_framework import serializers
from .models import ChatRequest, DirectMessage


class InitiateChatRequestSerializer(serializers.Serializer):
    """Input: student initiates a DM request to a senior based on a resolved query."""
    student_id = serializers.UUIDField()
    senior_id = serializers.UUIDField()
    query_id = serializers.UUIDField()


class ChatRequestResponseSerializer(serializers.ModelSerializer):
    """Output: details of a ChatRequest."""
    student_id = serializers.UUIDField(source='student_id', read_only=True)
    senior_id = serializers.UUIDField(source='senior_id', read_only=True)
    query_id = serializers.UUIDField(source='query_id', read_only=True)

    class Meta:
        model = ChatRequest
        fields = ['id', 'student_id', 'senior_id', 'query_id', 'intro_message', 'status', 'created_at', 'responded_at']
        read_only_fields = fields


class RespondChatRequestSerializer(serializers.Serializer):
    """Input: senior accepts or rejects a pending chat request."""
    ACTION_CHOICES = ['ACCEPT', 'REJECT']
    action = serializers.ChoiceField(choices=ACTION_CHOICES)


class SendMessageSerializer(serializers.Serializer):
    """Input: sending a message within an accepted chat thread."""
    sender_id = serializers.UUIDField()
    content = serializers.CharField(min_length=1)


class DirectMessageSerializer(serializers.ModelSerializer):
    """Output: single message in a thread."""
    sender_id = serializers.UUIDField(source='sender_id', read_only=True)
    sender_name = serializers.CharField(source='sender.name', read_only=True)

    class Meta:
        model = DirectMessage
        fields = ['id', 'sender_id', 'sender_name', 'content', 'sent_at']
        read_only_fields = fields

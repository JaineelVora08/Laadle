from django.db import models
from django.conf import settings
import uuid


class ChatRequest(models.Model):
    """
    Represents a student's request to DM a senior after a query is resolved.
    The senior must ACCEPT before any further messages can be exchanged.
    """

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='dm_requests_sent',
    )
    senior = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='dm_requests_received',
    )
    query = models.ForeignKey(
        'query_orchestrator.Query', on_delete=models.CASCADE,
        related_name='chat_requests',
        null=True, blank=True,
    )
    intro_message = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    domain_name = models.CharField(max_length=255, blank=True, default='',
                                   help_text='Domain context for queryless connect requests')

    class Meta:
        app_label = 'direct_messaging_service'
        ordering = ['-created_at']

    def __str__(self):
        return f"ChatRequest {self.id} [{self.status}] {self.student_id} → {self.senior_id}"


class DirectMessage(models.Model):
    """
    Individual message within an accepted chat thread.
    Only allowed when the parent ChatRequest.status == ACCEPTED.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_request = models.ForeignKey(
        ChatRequest, on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='dm_messages_sent',
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'direct_messaging_service'
        ordering = ['sent_at']

    def __str__(self):
        return f"DM {self.id} by {self.sender_id} at {self.sent_at}"

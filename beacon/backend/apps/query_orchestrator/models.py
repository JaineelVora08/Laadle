from django.db import models
from django.conf import settings
import uuid


class Query(models.Model):
    """Stores a student query and its resolution state."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='queries'
    )
    domain_id = models.UUIDField()
    content = models.TextField()
    embedding_vector_id = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rag_response = models.TextField(blank=True, default='')
    final_response = models.TextField(blank=True, default='')
    follow_up_questions = models.JSONField(default=list)
    matched_seniors = models.JSONField(default=list)
    is_resolved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'query_orchestrator'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Query {self.id} by {self.student_id} — {self.status}"


class ConflictRecord(models.Model):
    """Stores detected conflicts between senior advice items."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='conflicts')
    new_advice = models.TextField()
    conflicting_advice = models.TextField()
    flagged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'query_orchestrator'

    def __str__(self):
        return f"Conflict on Query {self.query_id} at {self.flagged_at}"


class SeniorQueryAssignment(models.Model):
    """Tracks which seniors are assigned to which queries."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RESPONDED', 'Responded'),
        ('SKIPPED', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='assignments')
    senior = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='query_assignments'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    advice_content = models.TextField(blank=True, default='')
    answered_followups = models.JSONField(default=list)
    trust_score_at_response = models.FloatField(default=0.0)
    similarity_score = models.FloatField(default=0.0)
    responded_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'query_orchestrator'
        unique_together = ('query', 'senior')

    def __str__(self):
        return f"Assignment {self.senior_id} → Query {self.query_id} [{self.status}]"

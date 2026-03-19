from django.db import models
from django.conf import settings
import uuid


class QueryCluster(models.Model):
    """Groups semantically similar pending queries so seniors answer once."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    representative_content = models.TextField(
        help_text='Consolidated question shown to seniors'
    )
    domain_ids = models.JSONField(default=list, help_text='Union of child query domain_ids')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    final_response = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'query_orchestrator'
        ordering = ['-created_at']

    def __str__(self):
        count = self.queries.count()
        return f"Cluster {self.id} ({count} queries) — {self.status}"


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
    domain_ids = models.JSONField(default=list, help_text='List of domain ID strings')
    content = models.TextField()
    embedding_vector_id = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rag_response = models.TextField(blank=True, default='')
    final_response = models.TextField(blank=True, default='')
    follow_up_questions = models.JSONField(default=list)
    matched_seniors = models.JSONField(default=list)
    is_resolved = models.BooleanField(default=False)
    student_rating = models.IntegerField(null=True, blank=True, help_text='Student rating 1-5')
    follow_through_success = models.BooleanField(null=True, blank=True, help_text='Did the advice help?')
    follow_through_proof = models.URLField(blank=True, default='', help_text='Optional proof URL')
    timestamp = models.DateTimeField(auto_now_add=True)

    # ── Query-compaction fields ──
    cluster = models.ForeignKey(
        QueryCluster, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='queries',
        help_text='Cluster this query belongs to (null = standalone)'
    )
    is_cluster_lead = models.BooleanField(
        default=False,
        help_text='True for the first query that created the cluster pipeline'
    )
    response_deadline = models.DateTimeField(
        null=True, blank=True,
        help_text='Deadline for senior responses (default: 24h after creation)'
    )
    response_window_hours = models.FloatField(
        default=24.0,
        help_text='Hours to wait for senior responses before auto-finalize'
    )
    FINALIZED_BY_CHOICES = [
        ('STUDENT', 'Student early finalization'),
        ('DEADLINE', 'Response window expired'),
        ('ALL_RESPONDED', 'All assigned seniors responded'),
    ]
    finalized_by = models.CharField(
        max_length=20, choices=FINALIZED_BY_CHOICES,
        null=True, blank=True,
        help_text='How the query was finalized (null = not yet finalized)'
    )

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
    faq_completed = models.BooleanField(
        default=False,
        help_text='True when senior has completed both Step 1 (advice) and Step 2 (FAQs)'
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'query_orchestrator'
        unique_together = ('query', 'senior')

    def __str__(self):
        return f"Assignment {self.senior_id} → Query {self.query_id} [{self.status}]"

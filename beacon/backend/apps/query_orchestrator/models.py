from django.db import models
import uuid


class Query(models.Model):
    """
    Stores a student query and its resolution state.
    Fields: id (UUID), student_id, domain_id, content, timestamp,
            is_resolved, rag_response, final_response, related_query_ids
    """
    pass


class ConflictRecord(models.Model):
    """
    Stores detected conflicts between senior advice items.
    Fields: id, query_id, new_advice, conflicting_advice, flagged_at
    """
    pass

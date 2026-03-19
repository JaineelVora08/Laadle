"""
Query Orchestrator Test Script
================================
Tests: Models (Query, ConflictRecord, SeniorQueryAssignment),
       Serializers, and Orchestrator pipeline logic.

Run with:
    python manage.py test query_orchestrator --testrunner=django.test.runner.DiscoverRunner

Or standalone:
    python manage.py shell < test_query_orchestrator.py

Prerequisites:
    - PostgreSQL running and migrated
    - At least 1 User in auth_service (or we create test users)
    - Neo4j running (for MentorMatchingEngine, or we mock it)
"""
import sys
import os
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beacon.settings')
import django
django.setup()

from django.utils import timezone
from apps.auth_service.models import User
from apps.query_orchestrator.models import Query, ConflictRecord, SeniorQueryAssignment
from apps.query_orchestrator.serializers import (
    QuerySubmitRequestSerializer,
    QuerySubmitResponseSerializer,
    SeniorResponseRequestSerializer,
    SeniorResponseStep1ResponseSerializer,
    SeniorFAQResponseRequestSerializer,
    FinalAdviceResponseSerializer,
    QueryStatusResponseSerializer,
    FollowUpRequestSerializer,
    FollowUpResponseSerializer,
    AnsweredFollowupSerializer,
    ContributingSeniorSerializer,
)

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name} — {detail}")


# ═══════════════════════════════════════════════
# SETUP: Create test users
# ═══════════════════════════════════════════════
print("\n── Setup: Creating test users ──")

try:
    student = User.objects.create_user(
        email=f'test_student_{uuid.uuid4().hex[:6]}@test.com',
        password='testpass123',
        name='Test Student',
        role='STUDENT',
    )
    test("Created test student", student.id is not None)

    senior = User.objects.create_user(
        email=f'test_senior_{uuid.uuid4().hex[:6]}@test.com',
        password='testpass123',
        name='Test Senior',
        role='SENIOR',
        trust_score=0.85,
    )
    test("Created test senior", senior.id is not None)

    senior2 = User.objects.create_user(
        email=f'test_senior2_{uuid.uuid4().hex[:6]}@test.com',
        password='testpass123',
        name='Test Senior 2',
        role='SENIOR',
        trust_score=0.72,
    )
    test("Created test senior 2", senior2.id is not None)
except Exception as e:
    test("Create test users", False, str(e))
    print("FATAL: Cannot proceed without test users")
    sys.exit(1)

domain_id = str(uuid.uuid4())

print()

# ═══════════════════════════════════════════════
# TEST GROUP 1: Models — CRUD
# ═══════════════════════════════════════════════
print("── Models: Query CRUD ──")

query = Query.objects.create(
    student=student,
    domain_id=domain_id,
    content="How do I start learning machine learning?",
    status='PENDING',
    rag_response='Start with Andrew Ng course...',
    follow_up_questions=['What math do I need?', 'Best online resources?'],
    matched_seniors=[str(senior.id), str(senior2.id)],
)
test("Create Query", query.id is not None)
test("Query status is PENDING", query.status == 'PENDING')
test("Query content stored", 'machine learning' in query.content)
test("Query follow_up_questions is list", isinstance(query.follow_up_questions, list))
test("Query matched_seniors is list", isinstance(query.matched_seniors, list))
test("Query ordering is -timestamp", Query._meta.ordering == ['-timestamp'])

# ConflictRecord
conflict = ConflictRecord.objects.create(
    query=query,
    new_advice="Skip math, just use libraries",
    conflicting_advice="Math is essential for ML",
)
test("Create ConflictRecord", conflict.id is not None)
test("ConflictRecord FK to Query", conflict.query_id == query.id)

# Verify query.conflicts reverse relation
test("Query.conflicts reverse relation", query.conflicts.count() == 1)

# SeniorQueryAssignment
assignment1 = SeniorQueryAssignment.objects.create(
    query=query,
    senior=senior,
)
test("Create SeniorQueryAssignment", assignment1.id is not None)
test("Assignment status default PENDING", assignment1.status == 'PENDING')

assignment2 = SeniorQueryAssignment.objects.create(
    query=query,
    senior=senior2,
)
test("Create second assignment", assignment2.id is not None)

# Test unique_together constraint
try:
    SeniorQueryAssignment.objects.create(query=query, senior=senior)
    test("unique_together constraint", False, "Should have raised IntegrityError")
except Exception:
    test("unique_together constraint blocks duplicate", True)

# Update assignment
assignment1.advice_content = "Start with Python basics, then learn scikit-learn"
assignment1.status = 'RESPONDED'
assignment1.responded_at = timezone.now()
assignment1.trust_score_at_response = senior.trust_score
assignment1.save()
test("Update assignment to RESPONDED", assignment1.status == 'RESPONDED')

# Verify select_related
assignments = SeniorQueryAssignment.objects.filter(
    query=query, status='RESPONDED'
).select_related('query')
test("select_related works", len(assignments) == 1 and assignments[0].query.content == query.content)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 2: Serializers
# ═══════════════════════════════════════════════
print("── Serializers ──")

# QuerySubmitRequestSerializer
s = QuerySubmitRequestSerializer(data={
    'student_id': str(student.id),
    'domain_id': domain_id,
    'content': 'How to learn ML?',
})
test("QuerySubmitRequestSerializer valid", s.is_valid())

s_bad = QuerySubmitRequestSerializer(data={
    'student_id': 'not-a-uuid',
    'domain_id': domain_id,
    'content': 'test',
})
test("QuerySubmitRequestSerializer rejects bad UUID", not s_bad.is_valid())

# QuerySubmitResponseSerializer
s = QuerySubmitResponseSerializer(data={
    'query_id': str(query.id),
    'status': 'PENDING',
    'provisional_answer': 'Start with Andrew Ng course...',
    'follow_up_questions': ['What math?'],
    'matched_seniors': [str(senior.id)],
    'timestamp': timezone.now().isoformat(),
})
test("QuerySubmitResponseSerializer valid", s.is_valid())

# SeniorResponseRequestSerializer
s = SeniorResponseRequestSerializer(data={
    'senior_id': str(senior.id),
    'advice_content': 'Learn Python first',
})
test("SeniorResponseRequestSerializer valid", s.is_valid())

# AnsweredFollowupSerializer
s = AnsweredFollowupSerializer(data={
    'question': 'What math?',
    'answer': 'Linear algebra and calculus',
})
test("AnsweredFollowupSerializer valid", s.is_valid())

# SeniorFAQResponseRequestSerializer
s = SeniorFAQResponseRequestSerializer(data={
    'senior_id': str(senior.id),
    'faq_answers': [
        {'question': 'What math?', 'answer': 'Linear algebra'},
        {'question': 'Best tools?', 'answer': 'Jupyter, scikit-learn'},
    ],
})
test("SeniorFAQResponseRequestSerializer valid", s.is_valid())

# ContributingSeniorSerializer
s = ContributingSeniorSerializer(data={
    'senior_id': str(senior.id),
    'trust_score': 0.85,
    'weight': 0.68,
})
test("ContributingSeniorSerializer valid", s.is_valid())

# FinalAdviceResponseSerializer
s = FinalAdviceResponseSerializer(data={
    'query_id': str(query.id),
    'final_answer': 'Synthesized answer here',
    'agreements': ['Both recommend Python'],
    'disagreements': [],
    'conflict_detected': False,
    'conflict_details': None,
    'contributing_seniors': [
        {'senior_id': str(senior.id), 'trust_score': 0.85, 'weight': 0.68}
    ],
})
test("FinalAdviceResponseSerializer valid", s.is_valid())

# QueryStatusResponseSerializer
s = QueryStatusResponseSerializer(data={
    'query_id': str(query.id),
    'status': 'PENDING',
    'provisional_answer': None,
    'final_answer': None,
    'follow_up_questions': [],
    'conflict_detected': False,
})
test("QueryStatusResponseSerializer valid", s.is_valid())

# FollowUpRequestSerializer
s = FollowUpRequestSerializer(data={
    'student_id': str(student.id),
    'content': 'What about deep learning?',
})
test("FollowUpRequestSerializer valid", s.is_valid())

# FollowUpResponseSerializer
s = FollowUpResponseSerializer(data={
    'answer': 'Deep learning uses neural networks',
    'source': 'INSTANT_SENIOR_MATCH',
    'confidence': 0.92,
})
test("FollowUpResponseSerializer valid", s.is_valid())

s = FollowUpResponseSerializer(data={
    'answer': None,
    'source': 'PENDING_SENIOR',
    'message': 'Senior notified',
})
test("FollowUpResponseSerializer valid (pending)", s.is_valid())

print()

# ═══════════════════════════════════════════════
# TEST GROUP 3: Query Status Flow
# ═══════════════════════════════════════════════
print("── Query Status Flow ──")

# Mark query resolved
query.final_response = "Synthesized ML learning path"
query.status = 'RESOLVED'
query.is_resolved = True
query.save()

query.refresh_from_db()
test("Query status updated to RESOLVED", query.status == 'RESOLVED')
test("Query is_resolved = True", query.is_resolved)
test("Query final_response saved", 'ML learning path' in query.final_response)

# Verify conflicts.exists()
test("Query has conflicts", query.conflicts.exists())

print()

# ═══════════════════════════════════════════════
# TEST GROUP 4: InternalQueryClient shape
# ═══════════════════════════════════════════════
print("── InternalQueryClient ──")

from apps.query_orchestrator.services.client import InternalQueryClient
client = InternalQueryClient()
test("InternalQueryClient instantiation", client is not None)
test("InternalQueryClient has submit_query()", hasattr(client, 'submit_query'))
test("InternalQueryClient has get_query_status()", hasattr(client, 'get_query_status'))

print()

# ═══════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════
print("── Cleanup ──")
try:
    SeniorQueryAssignment.objects.filter(query=query).delete()
    ConflictRecord.objects.filter(query=query).delete()
    query.delete()
    student.delete()
    senior.delete()
    senior2.delete()
    print("  ✓ Test data cleaned up")
except Exception as e:
    print(f"  ⊘ Cleanup partial: {e}")

print()

# ═══════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════
total = passed + failed
print("=" * 50)
if failed == 0:
    print(f"🎉 ALL {total} TESTS PASSED!")
else:
    print(f"Results: {passed}/{total} passed, {failed} failed")
print("=" * 50)

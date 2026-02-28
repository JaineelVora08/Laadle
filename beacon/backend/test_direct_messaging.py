"""
Direct Messaging Service Test Script
======================================
Tests: Models (ChatRequest, DirectMessage), Serializers,
       IntroMessageGenerator, and view business-logic rules.

Run with:
    python manage.py shell < test_direct_messaging.py

Prerequisites:
    - Migrations applied (python manage.py migrate)
    - GEMINI_API_KEY in settings (intro-generator live test skips if absent)
"""
import sys
import os
import uuid
import unittest.mock as mock
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beacon.settings')
import django
django.setup()

from django.utils import timezone
from django.conf import settings

from apps.auth_service.models import User
from apps.query_orchestrator.models import Query
from apps.direct_messaging_service.models import ChatRequest, DirectMessage

passed = 0
failed = 0
skipped = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name} — {detail}")


def skip(name, reason=""):
    global skipped
    skipped += 1
    print(f"  ⊘ {name} — SKIPPED ({reason})")


has_gemini = bool(getattr(settings, 'GEMINI_API_KEY', ''))

# ════════════════════════════════════════════════════
# SETUP: Create shared test fixtures
# ════════════════════════════════════════════════════
print("\n── Setup: Test fixtures ──")

uid = uuid.uuid4().hex[:6]

try:
    student = User.objects.create_user(
        email=f'dm_student_{uid}@test.com',
        password='testpass123',
        name='DM Student',
        role='STUDENT',
        current_level='Sophomore',
    )
    test("Created student", student.id is not None)

    senior = User.objects.create_user(
        email=f'dm_senior_{uid}@test.com',
        password='testpass123',
        name='DM Senior',
        role='SENIOR',
        trust_score=0.88,
    )
    test("Created senior", senior.id is not None)

    senior2 = User.objects.create_user(
        email=f'dm_senior2_{uid}@test.com',
        password='testpass123',
        name='DM Senior 2',
        role='SENIOR',
        trust_score=0.72,
    )
    test("Created senior2", senior2.id is not None)

except Exception as e:
    test("Create test users", False, str(e))
    print("FATAL: Cannot proceed without test users.")
    sys.exit(1)

domain_id = str(uuid.uuid4())

try:
    query = Query.objects.create(
        student=student,
        domain_id=domain_id,
        content="How do I break into software engineering?",
        status='RESOLVED',
        is_resolved=True,
        matched_seniors=[str(senior.id), str(senior2.id)],
        final_response="Focus on fundamentals and build projects.",
    )
    test("Created resolved Query", query.id is not None)
    test("Query status is RESOLVED", query.status == 'RESOLVED')
except Exception as e:
    test("Create resolved Query", False, str(e))
    print("FATAL: Cannot proceed without Query.")
    sys.exit(1)

print()

# ════════════════════════════════════════════════════
# TEST GROUP 1: ChatRequest model
# ════════════════════════════════════════════════════
print("── ChatRequest Model ──")

cr = ChatRequest.objects.create(
    student=student,
    senior=senior,
    query=query,
    intro_message="Hi, I'm DM Student and I'd love to connect.",
    status='PENDING',
)
test("Create ChatRequest", cr.id is not None)
test("id is UUID",           isinstance(cr.id, uuid.UUID))
test("status defaults PENDING", cr.status == 'PENDING')
test("responded_at is None", cr.responded_at is None)
test("intro_message stored", 'DM Student' in cr.intro_message)
test("student FK correct",   cr.student_id == student.id)
test("senior FK correct",    cr.senior_id == senior.id)
test("query FK correct",     cr.query_id == query.id)
test("__str__ includes id",  str(cr.id)[:8] in str(cr))

# Reverse relations
test("query.chat_requests reverse relation", query.chat_requests.count() == 1)
test("student.dm_requests_sent reverse",    student.dm_requests_sent.count() == 1)
test("senior.dm_requests_received reverse", senior.dm_requests_received.count() == 1)

# Ordering
cr2 = ChatRequest.objects.create(
    student=student,
    senior=senior2,
    query=query,
    intro_message="Hi from student to senior2",
    status='PENDING',
)
ordered = list(ChatRequest.objects.filter(student=student))
test("Ordering: newest first",
     ordered[0].created_at >= ordered[1].created_at)

# unique_together: duplicate (student, senior, query) must fail
try:
    ChatRequest.objects.create(
        student=student, senior=senior, query=query,
        intro_message="Duplicate attempt",
    )
    test("unique_together blocks duplicate ChatRequest", False, "No exception raised")
except Exception:
    test("unique_together blocks duplicate ChatRequest", True)

print()

# ════════════════════════════════════════════════════
# TEST GROUP 2: status transitions
# ════════════════════════════════════════════════════
print("── ChatRequest Status Transitions ──")

cr.status = 'ACCEPTED'
cr.responded_at = timezone.now()
cr.save()
cr.refresh_from_db()
test("Transition → ACCEPTED",         cr.status == 'ACCEPTED')
test("responded_at set after accept", cr.responded_at is not None)

cr2.status = 'REJECTED'
cr2.responded_at = timezone.now()
cr2.save()
cr2.refresh_from_db()
test("Transition → REJECTED",         cr2.status == 'REJECTED')
test("responded_at set after reject", cr2.responded_at is not None)

print()

# ════════════════════════════════════════════════════
# TEST GROUP 3: DirectMessage model
# ════════════════════════════════════════════════════
print("── DirectMessage Model ──")

msg1 = DirectMessage.objects.create(
    chat_request=cr,     # cr is ACCEPTED
    sender=student,
    content="Hi senior, nice to meet you!",
)
test("Create DirectMessage (student → senior)", msg1.id is not None)
test("id is UUID",                              isinstance(msg1.id, uuid.UUID))
test("content stored",                          'senior' in msg1.content)
test("sender FK is student",                    msg1.sender_id == student.id)
test("chat_request FK correct",                 msg1.chat_request_id == cr.id)
test("sent_at auto-set",                        msg1.sent_at is not None)
test("__str__ includes sender id",              str(msg1.sender_id)[:6] in str(msg1))

msg2 = DirectMessage.objects.create(
    chat_request=cr,
    sender=senior,
    content="Great to meet you! Let's get started.",
)
test("Create DirectMessage (senior → student)", msg2.id is not None)

# Ordering: oldest first
msgs = list(cr.messages.all())
test("Messages ordered oldest first",     msgs[0].sent_at <= msgs[1].sent_at)
test("messages reverse relation works",   cr.messages.count() == 2)

print()

# ════════════════════════════════════════════════════
# TEST GROUP 4: Business-rule enforcement (direct ORM level)
# ════════════════════════════════════════════════════
print("── Business Rules ──")

# Rule: messages can only be sent when ACCEPTED (cr2 is REJECTED)
# We test this at view level below; at model level DirectMessage has no guard — that's the view's job.
# So here we just verify the view-level check works via the serializer/view logic path.

# Verify ChatRequest.status choices are correct
choices = dict(ChatRequest.STATUS_CHOICES)
test("STATUS_CHOICES contains PENDING",   'PENDING' in choices)
test("STATUS_CHOICES contains ACCEPTED",  'ACCEPTED' in choices)
test("STATUS_CHOICES contains REJECTED",  'REJECTED' in choices)

# Verify query.is_resolved flag is checked (view logic guard test — simulate with query)
unresolved_query = Query.objects.create(
    student=student,
    domain_id=domain_id,
    content="An unresolved query",
    status='IN_PROGRESS',
    is_resolved=False,
    matched_seniors=[str(senior.id)],
)
test("Unresolved query created for guard test",
     not unresolved_query.is_resolved and unresolved_query.status != 'RESOLVED')

print()

# ════════════════════════════════════════════════════
# TEST GROUP 5: Serializers
# ════════════════════════════════════════════════════
print("── Serializers ──")

from apps.direct_messaging_service.serializers import (
    InitiateChatRequestSerializer,
    ChatRequestResponseSerializer,
    RespondChatRequestSerializer,
    SendMessageSerializer,
    DirectMessageSerializer,
)

# InitiateChatRequestSerializer
s = InitiateChatRequestSerializer(data={
    'student_id': str(student.id),
    'senior_id':  str(senior.id),
    'query_id':   str(query.id),
})
test("InitiateChatRequestSerializer valid",        s.is_valid(), str(s.errors))
test("InitiateChatRequestSerializer: student_id",  s.validated_data['student_id'] == student.id)
test("InitiateChatRequestSerializer: senior_id",   s.validated_data['senior_id'] == senior.id)

bad = InitiateChatRequestSerializer(data={
    'student_id': 'not-a-uuid',
    'senior_id':  str(senior.id),
    'query_id':   str(query.id),
})
test("InitiateChatRequestSerializer rejects bad UUID", not bad.is_valid())

missing = InitiateChatRequestSerializer(data={'student_id': str(student.id)})
test("InitiateChatRequestSerializer rejects missing fields", not missing.is_valid())

# ChatRequestResponseSerializer
s = ChatRequestResponseSerializer(cr)
data = s.data
test("ChatRequestResponseSerializer: has id",           'id' in data)
test("ChatRequestResponseSerializer: has intro_message",'intro_message' in data)
test("ChatRequestResponseSerializer: has status",       'status' in data)
test("ChatRequestResponseSerializer: status = ACCEPTED",data['status'] == 'ACCEPTED')
test("ChatRequestResponseSerializer: responded_at set", data['responded_at'] is not None)

# RespondChatRequestSerializer
s = RespondChatRequestSerializer(data={'action': 'ACCEPT'})
test("RespondChatRequestSerializer ACCEPT valid",        s.is_valid())

s = RespondChatRequestSerializer(data={'action': 'REJECT'})
test("RespondChatRequestSerializer REJECT valid",        s.is_valid())

s = RespondChatRequestSerializer(data={'action': 'IGNORE'})
test("RespondChatRequestSerializer rejects invalid action", not s.is_valid())

s = RespondChatRequestSerializer(data={})
test("RespondChatRequestSerializer rejects missing action", not s.is_valid())

# SendMessageSerializer
s = SendMessageSerializer(data={'sender_id': str(student.id), 'content': 'Hello!'})
test("SendMessageSerializer valid",                   s.is_valid())
test("SendMessageSerializer: content stored",         s.validated_data['content'] == 'Hello!')

s = SendMessageSerializer(data={'sender_id': str(student.id), 'content': ''})
test("SendMessageSerializer rejects empty content",   not s.is_valid())

s = SendMessageSerializer(data={'sender_id': 'bad-uuid', 'content': 'hi'})
test("SendMessageSerializer rejects bad sender_id",   not s.is_valid())

# DirectMessageSerializer
s = DirectMessageSerializer(msg1)
data = s.data
test("DirectMessageSerializer: has id",          'id' in data)
test("DirectMessageSerializer: has sender_id",   'sender_id' in data)
test("DirectMessageSerializer: has sender_name", 'sender_name' in data)
test("DirectMessageSerializer: has content",     'content' in data)
test("DirectMessageSerializer: has sent_at",     'sent_at' in data)
test("DirectMessageSerializer: sender_name = 'DM Student'",
     data['sender_name'] == 'DM Student')
test("DirectMessageSerializer: content correct", 'senior' in data['content'])

# Serializer list output
msgs_data = DirectMessageSerializer(cr.messages.all(), many=True).data
test("DirectMessageSerializer many=True returns list",   isinstance(msgs_data, list))
test("DirectMessageSerializer many=True returns 2 items", len(msgs_data) == 2)

print()

# ════════════════════════════════════════════════════
# TEST GROUP 6: IntroMessageGenerator
# ════════════════════════════════════════════════════
print("── IntroMessageGenerator ──")

from apps.direct_messaging_service.intro_generator import IntroMessageGenerator

gen = IntroMessageGenerator()
test("IntroMessageGenerator instantiation", gen is not None)
test("IntroMessageGenerator has generate()", hasattr(gen, 'generate'))

# Test fallback path when Gemini fails
with mock.patch.object(gen.client.models, 'generate_content', side_effect=Exception("API error")):
    fallback_intro = gen.generate(student=student, query=query, domain_name="Software Engineering")

test("Fallback intro is a non-empty string",       isinstance(fallback_intro, str) and len(fallback_intro) > 0)
test("Fallback intro mentions student name",        student.name in fallback_intro)

# Test mocked success path
mock_response = mock.MagicMock()
mock_response.text = (
    "Hi, I'm DM Student, a Sophomore interested in software engineering. "
    "I recently asked about breaking into the field and found your answer really insightful. "
    "I'd love to connect!"
)
with mock.patch.object(gen.client.models, 'generate_content', return_value=mock_response):
    mocked_intro = gen.generate(student=student, query=query, domain_name="Software Engineering")

test("Mocked intro returned correctly",   mocked_intro == mock_response.text.strip())
test("Mocked intro is non-empty string",  len(mocked_intro) > 0)

# Test with student missing extended profile (should not crash)
bare_student = User.objects.create_user(
    email=f'bare_{uid}@test.com',
    password='testpass123',
    name='Bare Student',
    role='STUDENT',
)
with mock.patch.object(gen.client.models, 'generate_content', return_value=mock_response):
    intro_no_profile = gen.generate(student=bare_student, query=query, domain_name="ML")
test("generate() handles student with no profile", isinstance(intro_no_profile, str))

# Live Gemini call
if has_gemini:
    try:
        live_intro = gen.generate(student=student, query=query, domain_name="Software Engineering")
        test("Live intro is a non-empty string",  isinstance(live_intro, str) and len(live_intro) > 0)
        test("Live intro is under 500 chars",     len(live_intro) < 500)
    except Exception as e:
        test("Live intro generation", False, str(e))
else:
    skip("Live intro generation", "GEMINI_API_KEY not set")

print()

# ════════════════════════════════════════════════════
# TEST GROUP 7: View logic — simulate initiate guard checks
# ════════════════════════════════════════════════════
print("── View Logic Guard Checks ──")

from rest_framework.test import APIRequestFactory
from apps.direct_messaging_service.views import (
    InitiateChatRequestView,
    RespondChatRequestView,
    MessageListCreateView,
    ChatRequestListView,
)

factory = APIRequestFactory()

# 7a: Initiate with unresolved query → 400
request = factory.post('/api/dm/initiate/', {
    'student_id': str(student.id),
    'senior_id':  str(senior.id),
    'query_id':   str(unresolved_query.id),
}, format='json')
request.user = student
response = InitiateChatRequestView.as_view()(request)
test("Initiate with unresolved query → 400",  response.status_code == 400)

# 7b: Initiate duplicate → 409 (cr already exists for this trio)
request = factory.post('/api/dm/initiate/', {
    'student_id': str(student.id),
    'senior_id':  str(senior.id),
    'query_id':   str(query.id),
}, format='json')
request.user = student
with mock.patch('apps.direct_messaging_service.views.IntroMessageGenerator') as MockGen:
    MockGen.return_value.generate.return_value = "Mocked intro"
    response = InitiateChatRequestView.as_view()(request)
test("Initiate duplicate → 409",  response.status_code == 409)

# 7c: Initiate with senior not in matched_seniors → 400
outsider = User.objects.create_user(
    email=f'outsider_{uid}@test.com',
    password='testpass123',
    name='Outsider Senior',
    role='SENIOR',
)
request = factory.post('/api/dm/initiate/', {
    'student_id': str(student.id),
    'senior_id':  str(outsider.id),
    'query_id':   str(query.id),
}, format='json')
request.user = student
with mock.patch('apps.direct_messaging_service.views.IntroMessageGenerator') as MockGen:
    MockGen.return_value.generate.return_value = "Mocked intro"
    response = InitiateChatRequestView.as_view()(request)
test("Initiate with unmatched senior → 400",  response.status_code == 400)

# 7d: Respond as wrong user (student tries to respond) → 403
request = factory.post(f'/api/dm/requests/{cr.id}/respond/', {'action': 'ACCEPT'}, format='json')
request.user = student   # student, not senior
response = RespondChatRequestView.as_view()(request, pk=cr.id)
test("Respond as non-senior participant → 403",  response.status_code == 403)

# 7e: Respond to already-decided request → 400
# cr is already ACCEPTED
request = factory.post(f'/api/dm/requests/{cr.id}/respond/', {'action': 'ACCEPT'}, format='json')
request.user = senior
response = RespondChatRequestView.as_view()(request, pk=cr.id)
test("Respond to already ACCEPTED request → 400",  response.status_code == 400)

# 7f: Send message on REJECTED request → 403
request = factory.post(f'/api/dm/requests/{cr2.id}/messages/', {
    'sender_id': str(student.id),
    'content': 'Hello?',
}, format='json')
request.user = student
response = MessageListCreateView.as_view()(request, pk=cr2.id)
test("Send message on REJECTED thread → 403",  response.status_code == 403)

# 7g: List messages as participant (cr is ACCEPTED, student is participant)
request = factory.get(f'/api/dm/requests/{cr.id}/messages/')
request.user = student
response = MessageListCreateView.as_view()(request, pk=cr.id)
test("List messages as participant → 200",    response.status_code == 200)
test("List messages returns list type",       isinstance(response.data, list))
test("List messages returns 2 items",         len(response.data) == 2)

# 7h: List messages as non-participant → 403
request = factory.get(f'/api/dm/requests/{cr.id}/messages/')
request.user = outsider
response = MessageListCreateView.as_view()(request, pk=cr.id)
test("List messages as non-participant → 403",  response.status_code == 403)

# 7i: Send valid message on ACCEPTED thread
request = factory.post(f'/api/dm/requests/{cr.id}/messages/', {
    'sender_id': str(senior.id),
    'content': 'Welcome aboard!',
}, format='json')
request.user = senior
response = MessageListCreateView.as_view()(request, pk=cr.id)
test("Send message on ACCEPTED thread → 201",  response.status_code == 201)
test("Response has content field",             'content' in response.data)
test("Response content correct",              'Welcome' in response.data['content'])

# 7j: ChatRequestListView — student sees outgoing
request = factory.get('/api/dm/requests/')
request.user = student
response = ChatRequestListView.as_view()(request)
test("Student list → 200",                response.status_code == 200)
test("Student sees only outgoing requests", all(
    str(item.get('student_id') or '') == str(student.id)
    for item in response.data
))

# 7k: ChatRequestListView — senior sees incoming
request = factory.get('/api/dm/requests/')
request.user = senior
response = ChatRequestListView.as_view()(request)
test("Senior list → 200",                 response.status_code == 200)
test("Senior sees only incoming requests", all(
    str(item.get('senior_id') or '') == str(senior.id)
    for item in response.data
))

print()

# ════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════
print("── Cleanup ──")
try:
    DirectMessage.objects.filter(chat_request__query=query).delete()
    ChatRequest.objects.filter(query=query).delete()
    unresolved_query.delete()
    query.delete()
    student.delete()
    senior.delete()
    senior2.delete()
    bare_student.delete()
    outsider.delete()
    print("  ✓ Test data cleaned up")
except Exception as e:
    print(f"  ⊘ Cleanup partial: {e}")

print()

# ════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════
total = passed + failed
print("=" * 50)
if failed == 0:
    print(f"🎉 ALL {total} TESTS PASSED! ({skipped} skipped)")
else:
    print(f"Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")
print("=" * 50)

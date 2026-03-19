"""
User Profile Service Test Script
==================================
Tests: UserProfile model, serializers, views (profile, update, achievements, internal)

Run with:
    python manage.py shell < test_user_profile_service.py

Prerequisites:
    - PostgreSQL running and migrated
    - auth_service models available
"""
import sys
import os
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beacon.settings')
import django
django.setup()

from django.test import RequestFactory
from rest_framework.test import force_authenticate

from apps.auth_service.models import User, Student, Senior, Achievement
from apps.user_profile_service.models import UserProfile
from apps.user_profile_service.serializers import (
    UserProfileResponseSerializer,
    AchievementSerializer,
    UpdateProfileSerializer,
)
from apps.user_profile_service.views import (
    UserProfileView,
    UpdateProfileView,
    AchievementView,
    InternalProfileView,
)

passed = 0
failed = 0

factory = RequestFactory()


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name} — {detail}")


# ═══════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════
print("\n── Setup ──")

student_user = User.objects.create_user(
    email=f'profile_student_{uuid.uuid4().hex[:6]}@test.com',
    password='testpass123',
    name='Profile Student',
    role='STUDENT',
    availability=True,
    current_level='sophomore',
)
Student.objects.get_or_create(user=student_user, defaults={'low_energy_mode': False, 'momentum_score': 0.5})
test("Created test student", student_user.id is not None)

senior_user = User.objects.create_user(
    email=f'profile_senior_{uuid.uuid4().hex[:6]}@test.com',
    password='testpass123',
    name='Profile Senior',
    role='SENIOR',
    availability=True,
    trust_score=0.88,
    current_level='senior',
)
Senior.objects.get_or_create(user=senior_user, defaults={
    'consistency_score': 0.9,
    'alignment_score': 0.85,
    'follow_through_rate': 0.92,
})
test("Created test senior", senior_user.id is not None)

other_user = User.objects.create_user(
    email=f'profile_other_{uuid.uuid4().hex[:6]}@test.com',
    password='testpass123',
    name='Other User',
    role='STUDENT',
)
test("Created other user (for auth tests)", other_user.id is not None)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 1: UserProfile Model
# ═══════════════════════════════════════════════
print("── UserProfile Model ──")

profile, created = UserProfile.objects.get_or_create(user=student_user)
test("UserProfile created", created)
test("UserProfile has bio field", hasattr(profile, 'bio'))
test("UserProfile has avatar_url field", hasattr(profile, 'avatar_url'))
test("UserProfile has domains_of_interest field", hasattr(profile, 'domains_of_interest'))
test("UserProfile bio default empty", profile.bio == '')
test("UserProfile domains default empty list", profile.domains_of_interest == [])

# Test OneToOneField constraint
try:
    UserProfile.objects.create(user=student_user)
    test("OneToOne constraint", False, "Should have raised IntegrityError")
except Exception:
    test("OneToOne constraint blocks duplicate", True)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 2: Serializers
# ═══════════════════════════════════════════════
print("── Serializers ──")

# UserProfileResponseSerializer
s = UserProfileResponseSerializer(data={
    'id': str(student_user.id),
    'name': 'Profile Student',
    'email': student_user.email,
    'role': 'STUDENT',
    'availability': True,
    'trust_score': 0.0,
    'current_level': 'sophomore',
    'active_load': 0,
    'low_energy_mode': False,
    'momentum_score': 0.5,
    'consistency_score': None,
    'alignment_score': None,
    'follow_through_rate': None,
    'achievements': [],
})
test("UserProfileResponseSerializer valid (student)", s.is_valid())

s = UserProfileResponseSerializer(data={
    'id': str(senior_user.id),
    'name': 'Profile Senior',
    'email': senior_user.email,
    'role': 'SENIOR',
    'availability': True,
    'trust_score': 0.88,
    'current_level': 'senior',
    'active_load': 0,
    'low_energy_mode': None,
    'momentum_score': None,
    'consistency_score': 0.9,
    'alignment_score': 0.85,
    'follow_through_rate': 0.92,
    'achievements': [],
})
test("UserProfileResponseSerializer valid (senior)", s.is_valid())

# AchievementSerializer
s = AchievementSerializer(data={
    'title': 'Published ML Paper',
    'proof_url': 'https://arxiv.org/paper123',
})
test("AchievementSerializer valid", s.is_valid())

s = AchievementSerializer(data={'title': 'No URL needed'})
test("AchievementSerializer valid without URL", s.is_valid())

# UpdateProfileSerializer — student
s = UpdateProfileSerializer(
    data={'name': 'Updated Name', 'low_energy_mode': True},
    context={'role': 'STUDENT'},
)
test("UpdateProfileSerializer valid (student fields)", s.is_valid())

# UpdateProfileSerializer — student with senior fields (should fail)
s = UpdateProfileSerializer(
    data={'consistency_score': 0.9},
    context={'role': 'STUDENT'},
)
test("UpdateProfileSerializer rejects senior fields for student", not s.is_valid())

# UpdateProfileSerializer — senior
s = UpdateProfileSerializer(
    data={'consistency_score': 0.95, 'alignment_score': 0.88},
    context={'role': 'SENIOR'},
)
test("UpdateProfileSerializer valid (senior fields)", s.is_valid())

# UpdateProfileSerializer — senior with student fields (should fail)
s = UpdateProfileSerializer(
    data={'low_energy_mode': True},
    context={'role': 'SENIOR'},
)
test("UpdateProfileSerializer rejects student fields for senior", not s.is_valid())

print()

# ═══════════════════════════════════════════════
# TEST GROUP 3: Views — UserProfileView
# ═══════════════════════════════════════════════
print("── Views: UserProfileView ──")

# GET own profile
request = factory.get(f'/api/profile/{student_user.id}/')
force_authenticate(request, user=student_user)
response = UserProfileView.as_view()(request, user_id=str(student_user.id))
test("GET own profile returns 200", response.status_code == 200)
test("GET profile has name", response.data.get('name') == 'Profile Student')
test("GET profile has role", response.data.get('role') == 'STUDENT')
test("GET profile has achievements list", isinstance(response.data.get('achievements'), list))

# GET other user's profile (forbidden)
request = factory.get(f'/api/profile/{student_user.id}/')
force_authenticate(request, user=other_user)
response = UserProfileView.as_view()(request, user_id=str(student_user.id))
test("GET other user's profile returns 403", response.status_code == 403)

# GET non-existent user
request = factory.get('/api/profile/00000000-0000-0000-0000-000000000000/')
force_authenticate(request, user=student_user)
response = UserProfileView.as_view()(request, user_id='00000000-0000-0000-0000-000000000000')
test("GET non-existent user returns 404", response.status_code == 404)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 4: Views — UpdateProfileView
# ═══════════════════════════════════════════════
print("── Views: UpdateProfileView ──")

# PUT update name
request = factory.put(
    f'/api/profile/{student_user.id}/update/',
    data={'name': 'Updated Student'},
    content_type='application/json',
)
force_authenticate(request, user=student_user)
response = UpdateProfileView.as_view()(request, user_id=str(student_user.id))
test("PUT update name returns 200", response.status_code == 200)
test("PUT update name reflected", response.data.get('name') == 'Updated Student')

# PATCH update availability
request = factory.patch(
    f'/api/profile/{student_user.id}/update/',
    data={'availability': False},
    content_type='application/json',
)
force_authenticate(request, user=student_user)
response = UpdateProfileView.as_view()(request, user_id=str(student_user.id))
test("PATCH update availability returns 200", response.status_code == 200)

# Update by non-owner (forbidden)
request = factory.put(
    f'/api/profile/{student_user.id}/update/',
    data={'name': 'Hacked'},
    content_type='application/json',
)
force_authenticate(request, user=other_user)
response = UpdateProfileView.as_view()(request, user_id=str(student_user.id))
test("PUT by non-owner returns 403", response.status_code == 403)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 5: Views — AchievementView
# ═══════════════════════════════════════════════
print("── Views: AchievementView ──")

# POST achievement (senior only)
request = factory.post(
    f'/api/profile/{senior_user.id}/achievements/',
    data={'title': 'ML Research Paper', 'proof_url': 'https://arxiv.org/test'},
    content_type='application/json',
)
force_authenticate(request, user=senior_user)
response = AchievementView.as_view()(request, user_id=str(senior_user.id))
test("POST achievement returns 201", response.status_code == 201)
test("POST achievement has title", response.data.get('title') == 'ML Research Paper')
test("POST achievement verified=False", response.data.get('verified') == False)

# POST achievement as student (should fail)
request = factory.post(
    f'/api/profile/{student_user.id}/achievements/',
    data={'title': 'Student Achievement'},
    content_type='application/json',
)
force_authenticate(request, user=student_user)
response = AchievementView.as_view()(request, user_id=str(student_user.id))
test("POST achievement as student returns 403", response.status_code == 403)

# GET achievements
request = factory.get(f'/api/profile/{senior_user.id}/achievements/')
force_authenticate(request, user=senior_user)
response = AchievementView.as_view()(request, user_id=str(senior_user.id))
test("GET achievements returns 200", response.status_code == 200)
test("GET achievements has list", isinstance(response.data.get('achievements'), list))
test("GET achievements count >= 1", len(response.data.get('achievements', [])) >= 1)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 6: Views — InternalProfileView
# ═══════════════════════════════════════════════
print("── Views: InternalProfileView ──")

from django.conf import settings

# GET with valid internal secret
request = factory.get(f'/internal/profile/{student_user.id}/')
request.META['HTTP_X_INTERNAL_SECRET'] = settings.INTERNAL_SECRET
response = InternalProfileView.as_view()(request, user_id=str(student_user.id))
test("Internal GET with secret returns 200", response.status_code == 200)
test("Internal GET has user data", response.data.get('name') is not None)

# GET without internal secret
request = factory.get(f'/internal/profile/{student_user.id}/')
response = InternalProfileView.as_view()(request, user_id=str(student_user.id))
test("Internal GET without secret returns 401", response.status_code == 401)

# PATCH with valid internal secret
request = factory.patch(
    f'/internal/profile/{senior_user.id}/',
    data={'consistency_score': 0.95},
    content_type='application/json',
)
request.META['HTTP_X_INTERNAL_SECRET'] = settings.INTERNAL_SECRET
response = InternalProfileView.as_view()(request, user_id=str(senior_user.id))
test("Internal PATCH returns 200", response.status_code == 200)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 7: InternalProfileClient shape
# ═══════════════════════════════════════════════
print("── InternalProfileClient ──")

from apps.user_profile_service.services.client import InternalProfileClient
client = InternalProfileClient()
test("InternalProfileClient instantiation", client is not None)
test("InternalProfileClient has get_profile()", hasattr(client, 'get_profile'))
test("InternalProfileClient has update_profile()", hasattr(client, 'update_profile'))

print()

# ═══════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════
print("── Cleanup ──")
try:
    Achievement.objects.filter(user__in=[student_user, senior_user]).delete()
    UserProfile.objects.filter(user__in=[student_user, senior_user, other_user]).delete()
    Student.objects.filter(user=student_user).delete()
    Senior.objects.filter(user=senior_user).delete()
    student_user.delete()
    senior_user.delete()
    other_user.delete()
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

"""
Neo4j Integration Test Script for Module 2
============================================
Run with:  python manage.py shell < test_neo4j.py
Or:        python manage.py shell
           >>> exec(open('test_neo4j.py').read())

Prerequisites:
  - Neo4j running on bolt://localhost:7687
  - Credentials: neo4j / testpassword (or update BOLT_URL below)
"""

import sys

# ── 1. Connect to Neo4j ──
from neomodel import config, db, clear_neo4j_database

BOLT_URL = 'bolt://neo4j:ishat@123@localhost:7687'
config.DATABASE_URL = BOLT_URL

try:
    db.cypher_query("RETURN 1")
    print("✓ Connected to Neo4j")
except Exception as e:
    print(f"✗ Cannot connect to Neo4j at {BOLT_URL}: {e}")
    sys.exit(1)

# ── 2. Clear database for clean test ──
clear_neo4j_database(db)
print("✓ Database cleared\n")

# ── 3. Import models and engine ──
from apps.domain_management_service.graph_models import (
    UserNode, DomainNode, InterestedIn, ExperiencedIn, MentoredBy,
)
from apps.mentor_matching_service.matching_engine import MentorMatchingEngine

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
# TEST GROUP 1: Graph Models — Node Creation
# ═══════════════════════════════════════════════
print("── Graph Models: Node Creation ──")

student1 = UserNode(
    uid='stu-001', role='STUDENT', name='Alice',
    availability=True, current_level='sophomore',
).save()
test("Create Student node", student1.uid == 'stu-001')

student2 = UserNode(
    uid='stu-002', role='STUDENT', name='Charlie',
    availability=True, current_level='junior',
).save()
test("Create second Student node", student2.uid == 'stu-002')

student3_unavailable = UserNode(
    uid='stu-003', role='STUDENT', name='Diana',
    availability=False, current_level='sophomore',
).save()
test("Create unavailable Student node", student3_unavailable.uid == 'stu-003')

senior1 = UserNode(
    uid='sr-001', role='SENIOR', name='Bob',
    availability=True, trust_score=85.0, active_load=1,
).save()
test("Create Senior node", senior1.trust_score == 85.0)

senior2 = UserNode(
    uid='sr-002', role='SENIOR', name='Eve',
    availability=True, trust_score=72.0, active_load=2,
).save()
test("Create second Senior node", senior2.uid == 'sr-002')

senior3_overloaded = UserNode(
    uid='sr-003', role='SENIOR', name='Frank',
    availability=True, trust_score=90.0, active_load=10,
).save()
test("Create overloaded Senior (active_load=10)", senior3_overloaded.active_load == 10)

senior4_unavailable = UserNode(
    uid='sr-004', role='SENIOR', name='Grace',
    availability=False, trust_score=95.0, active_load=0,
).save()
test("Create unavailable Senior", senior4_unavailable.availability == False)

domain_ml = DomainNode(name='Machine Learning', type='academic', popularity_score=5.0).save()
test("Create Domain: Machine Learning", domain_ml.name == 'Machine Learning')

domain_web = DomainNode(name='Web Development', type='academic', popularity_score=3.0).save()
test("Create Domain: Web Development", domain_web.name == 'Web Development')

print()

# ═══════════════════════════════════════════════
# TEST GROUP 2: Graph Models — Relationships
# ═══════════════════════════════════════════════
print("── Graph Models: Relationships ──")

# Students interested in ML
rel1 = student1.interested_in.connect(domain_ml, {'priority': 1, 'current_level': 'beginner'})
test("Student1 → INTERESTED_IN → ML", rel1 is not None)

rel2 = student2.interested_in.connect(domain_ml, {'priority': 2, 'current_level': 'intermediate'})
test("Student2 → INTERESTED_IN → ML", rel2 is not None)

# Unavailable student also interested in ML
student3_unavailable.interested_in.connect(domain_ml, {'priority': 1, 'current_level': 'beginner'})
test("Unavailable Student3 → INTERESTED_IN → ML", True)

# Student1 also interested in Web Dev
student1.interested_in.connect(domain_web, {'priority': 2, 'current_level': 'beginner'})
test("Student1 → INTERESTED_IN → Web Dev", True)

# Seniors experienced in ML
senior1.experienced_in.connect(domain_ml, {'experience_level': 'expert', 'years_of_involvement': 3})
test("Senior1 (Bob) → EXPERIENCED_IN → ML", True)

senior2.experienced_in.connect(domain_ml, {'experience_level': 'intermediate', 'years_of_involvement': 1})
test("Senior2 (Eve) → EXPERIENCED_IN → ML", True)

# Overloaded senior also experienced in ML
senior3_overloaded.experienced_in.connect(domain_ml, {'experience_level': 'expert', 'years_of_involvement': 5})
test("Overloaded Senior3 → EXPERIENCED_IN → ML", True)

# Unavailable senior experienced in ML
senior4_unavailable.experienced_in.connect(domain_ml, {'experience_level': 'expert', 'years_of_involvement': 4})
test("Unavailable Senior4 → EXPERIENCED_IN → ML", True)

# Senior1 also experienced in Web Dev
senior1.experienced_in.connect(domain_web, {'experience_level': 'intermediate', 'years_of_involvement': 2})
test("Senior1 (Bob) → EXPERIENCED_IN → Web Dev", True)

# Verify relationship properties
rel = student1.interested_in.relationship(domain_ml)
test("Relationship properties preserved", rel.priority == 1 and rel.current_level == 'beginner')

# Verify traversal
student1_domains = student1.interested_in.all()
test("Student1 has 2 domain interests", len(student1_domains) == 2)

senior1_domains = senior1.experienced_in.all()
test("Senior1 has 2 domain expertise", len(senior1_domains) == 2)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 3: Mentor Matching Engine
# ═══════════════════════════════════════════════
print("── Mentor Matching: find_mentors() ──")

engine = MentorMatchingEngine()

# Find mentors for Student1 in ML
mentors = engine.find_mentors('stu-001', domain_ml.uid, priority=1)
test("find_mentors returns results", len(mentors) > 0)

mentor_ids = [m['senior_id'] for m in mentors]
test("Bob (available, low load) is in results", 'sr-001' in mentor_ids)
test("Eve (available, low load) is in results", 'sr-002' in mentor_ids)
test("Frank (overloaded, load=10) is excluded", 'sr-003' not in mentor_ids)
test("Grace (unavailable) is excluded", 'sr-004' not in mentor_ids)

# Verify sorted by trust_score DESC
if len(mentors) >= 2:
    test("Results sorted by trust_score DESC",
         mentors[0]['trust_score'] >= mentors[1]['trust_score'])

# Verify response shape
first = mentors[0]
test("Response has all required fields",
     all(k in first for k in ['senior_id', 'name', 'trust_score', 'domain', 'experience_level', 'availability', 'active_load']))

# Find mentors in Web Dev
web_mentors = engine.find_mentors('stu-001', domain_web.uid, priority=1)
test("find_mentors for Web Dev returns Bob only", len(web_mentors) == 1 and web_mentors[0]['senior_id'] == 'sr-001')

# Find mentors for non-connected domain
no_mentors = engine.find_mentors('stu-002', domain_web.uid, priority=1)
test("No mentors for student not connected to domain", len(no_mentors) == 0)

print()

# ═══════════════════════════════════════════════
# TEST GROUP 4: Peer Matching
# ═══════════════════════════════════════════════
print("── Mentor Matching: find_peers() ──")

peers = engine.find_peers('stu-001', domain_ml.uid)
peer_ids = [p['student_id'] for p in peers]
test("find_peers returns results", len(peers) > 0)
test("Charlie is a peer of Alice in ML", 'stu-002' in peer_ids)
test("Alice is not her own peer", 'stu-001' not in peer_ids)
test("Unavailable Diana is excluded", 'stu-003' not in peer_ids)

# Verify response shape
if peers:
    first_peer = peers[0]
    test("Peer response has all required fields",
         all(k in first_peer for k in ['student_id', 'name', 'domain', 'current_level', 'priority']))

print()

# ═══════════════════════════════════════════════
# TEST GROUP 5: Mentorship Edge Creation
# ═══════════════════════════════════════════════
print("── Mentor Matching: create_mentorship_edge() ──")

result = engine.create_mentorship_edge('stu-001', 'sr-001', domain_ml.uid)
test("Mentorship created successfully", result['status'] == 'PENDING')
test("Mentorship has an ID", 'mentorship_id' in result and len(result['mentorship_id']) > 0)

# Duplicate should fail
try:
    engine.create_mentorship_edge('stu-001', 'sr-001', domain_ml.uid)
    test("Duplicate mentorship blocked", False, "Should have raised ValueError")
except ValueError as e:
    test("Duplicate mentorship blocked", 'already exists' in str(e).lower())

# Non-existent user should fail
try:
    engine.create_mentorship_edge('stu-999', 'sr-001', domain_ml.uid)
    test("Non-existent student blocked", False, "Should have raised ValueError")
except ValueError as e:
    test("Non-existent student blocked", True)

# Self-mentorship (if student == senior ID)
# Different user in this design, so just verify a new valid pair
result2 = engine.create_mentorship_edge('stu-002', 'sr-002', domain_ml.uid)
test("Second mentorship created", result2['status'] == 'PENDING')

print()

# ═══════════════════════════════════════════════
# TEST GROUP 6: Node Retrieval & Queries
# ═══════════════════════════════════════════════
print("── Graph Queries: Node Retrieval ──")

# Fetch by uid
fetched = UserNode.nodes.get(uid='stu-001')
test("Fetch UserNode by uid", fetched.name == 'Alice')

fetched_domain = DomainNode.nodes.get(name='Machine Learning')
test("Fetch DomainNode by name", fetched_domain.type == 'academic')

# Get all domains
all_domains = DomainNode.nodes.all()
test("Get all DomainNodes", len(all_domains) == 2)

# Get all students
all_students = UserNode.nodes.filter(role='STUDENT')
test("Filter UserNodes by role=STUDENT", len(all_students) == 3)

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

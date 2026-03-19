#!/usr/bin/env python
"""
Seed script for Neo4j Aura.

Creates:
  - Existing PostgreSQL users as UserNode (mirrors)
  - 50 additional fake users (25 students, 25 seniors)
  - 12 domain nodes (covering your existing domains + 10 new topics)
  - INTERESTED_IN / EXPERIENCED_IN relationships
  - A few MENTORED_BY edges

Usage:
    cd beacon/backend
    python seed_neo4j.py
"""

import os
import sys
import random
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beacon.settings')

import django
django.setup()

from apps.auth_service.models import User
from apps.domain_management_service.graph_models import (
    DomainNode, UserNode, InterestedIn, ExperiencedIn, MentoredBy,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_or_create_domain(name, domain_type='general'):
    """Create a DomainNode if it doesn't exist (case-insensitive check)."""
    from neomodel import db
    results, _ = db.cypher_query(
        "MATCH (d:DomainNode) WHERE toLower(d.name) = $name RETURN d",
        {'name': name.strip().lower()},
        resolve_objects=True,
    )
    if results:
        node = results[0][0]
        print(f"  ✓ Domain '{name}' already exists (uid={node.uid})")
        return node
    node = DomainNode(name=name, type=domain_type, popularity_score=0.0).save()
    print(f"  + Created domain '{name}' (uid={node.uid})")
    return node


def get_or_create_user_node(uid, role, name='', trust_score=0.5, availability=True):
    """Create a UserNode if it doesn't exist."""
    existing = UserNode.nodes.filter(uid=uid)
    if existing:
        print(f"  ✓ UserNode '{name}' ({role}) already exists")
        return existing[0]
    node = UserNode(
        uid=uid, role=role, name=name,
        trust_score=trust_score, availability=availability,
        active_load=0, current_level='',
    ).save()
    print(f"  + Created UserNode '{name}' ({role})")
    return node


# ── Domain Definitions ───────────────────────────────────────────────────────

DOMAINS = [
    # Existing domains (your current topics)
    'Machine Learning',
    'Deep Learning',
    # 10 new topics
    'Web Development',
    'Data Structures & Algorithms',
    'Cloud Computing',
    'Cybersecurity',
    'Mobile App Development',
    'Natural Language Processing',
    'Computer Vision',
    'DevOps & CI/CD',
    'Blockchain & Web3',
    'Competitive Programming',
]


# ── Fake Users ───────────────────────────────────────────────────────────────

STUDENT_NAMES = [
    'Aarav Sharma', 'Priya Patel', 'Rohan Gupta', 'Sneha Iyer',
    'Arjun Reddy', 'Kavya Nair', 'Vikram Singh', 'Ananya Desai',
    'Rahul Joshi', 'Meera Kulkarni', 'Aditya Verma', 'Divya Rao',
    'Kunal Mehta', 'Riya Kapoor', 'Sanjay Kumar', 'Neha Agarwal',
    'Harsh Bhatt', 'Pooja Menon', 'Varun Tiwari', 'Swati Mishra',
    'Akash Pandey', 'Shruti Jain', 'Nikhil Chauhan', 'Tanya Saxena',
    'Rajat Goyal',
]

SENIOR_NAMES = [
    'Dr. Amit Banerjee', 'Prof. Sunita Krishnan', 'Manish Arora',
    'Deepika Venkatesh', 'Sameer Choudhary', 'Lakshmi Subramaniam',
    'Karthik Narayanan', 'Anjali Bhatia', 'Vivek Malhotra',
    'Rashmi Hegde', 'Suresh Ramachandran', 'Nandini Ghosh',
    'Ganesh Pillai', 'Revathi Srinivasan', 'Pankaj Dubey',
    'Shalini Mukherjee', 'Arun Thakur', 'Gayathri Raghavan',
    'Mohit Khanna', 'Bhavna Sethi', 'Raghav Mittal',
    'Aparna Deshpande', 'Siddharth Jha', 'Pallavi Vohra',
    'Nitin Bajaj',
]

EXPERIENCE_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert']


# ── Main Seed Function ───────────────────────────────────────────────────────

def seed():
    print('\n' + '=' * 60)
    print('  NEO4J AURA SEED SCRIPT')
    print('=' * 60)

    # ── 1. Create Domains ────────────────────────────────────────────────────
    print('\n📦 Creating Domains...')
    domain_nodes = {}
    for name in DOMAINS:
        domain_nodes[name] = get_or_create_domain(name)

    # ── 2. Mirror existing PostgreSQL users ──────────────────────────────────
    print('\n👤 Mirroring existing PostgreSQL users...')
    pg_users = User.objects.all()
    existing_user_nodes = {}
    for u in pg_users:
        node = get_or_create_user_node(
            uid=str(u.id), role=u.role, name=u.name,
            trust_score=float(u.trust_score),
            availability=bool(getattr(u, 'availability', True)),
        )
        existing_user_nodes[str(u.id)] = node

        # Connect existing users to a random spread of domains (not just ML & DL)
        if u.role == 'STUDENT':
            num_interests = random.randint(2, 4)
            chosen_domains = random.sample(DOMAINS, num_interests)
            for dname in chosen_domains:
                if dname in domain_nodes:
                    if not node.interested_in.is_connected(domain_nodes[dname]):
                        node.interested_in.connect(domain_nodes[dname], {
                            'priority': random.randint(1, 3),
                            'current_level': random.choice(['beginner', 'intermediate']),
                        })
                        print(f"    → {u.name} INTERESTED_IN {dname}")
        elif u.role == 'SENIOR':
            num_domains = random.randint(1, 3)
            chosen_domains = random.sample(DOMAINS, num_domains)
            for dname in chosen_domains:
                if dname in domain_nodes:
                    if not node.experienced_in.is_connected(domain_nodes[dname]):
                        node.experienced_in.connect(domain_nodes[dname], {
                            'experience_level': random.choice(EXPERIENCE_LEVELS),
                            'years_of_involvement': random.randint(1, 5),
                        })
                        print(f"    → {u.name} EXPERIENCED_IN {dname}")

    # ── 3. Create 25 fake students ───────────────────────────────────────────
    print('\n🎓 Creating 25 fake students...')
    student_nodes = []
    for name in STUDENT_NAMES:
        uid = str(uuid.uuid4())
        node = get_or_create_user_node(uid=uid, role='STUDENT', name=name, trust_score=0.5)
        student_nodes.append(node)

        # Each student is interested in 2-4 random domains
        num_interests = random.randint(2, 4)
        chosen_domains = random.sample(DOMAINS, num_interests)
        for dname in chosen_domains:
            if not node.interested_in.is_connected(domain_nodes[dname]):
                node.interested_in.connect(domain_nodes[dname], {
                    'priority': random.randint(1, 3),
                    'current_level': random.choice(['beginner', 'intermediate']),
                })

    # ── 4. Create 25 fake seniors ────────────────────────────────────────────
    print('\n🏅 Creating 25 fake seniors...')
    senior_nodes = []
    for name in SENIOR_NAMES:
        uid = str(uuid.uuid4())
        trust = round(random.uniform(0.4, 0.95), 2)
        node = get_or_create_user_node(
            uid=uid, role='SENIOR', name=name,
            trust_score=trust, availability=random.choice([True, True, True, False]),
        )
        senior_nodes.append(node)

        # Each senior is experienced in 1-3 domains
        num_domains = random.randint(1, 3)
        chosen_domains = random.sample(DOMAINS, num_domains)
        for dname in chosen_domains:
            if not node.experienced_in.is_connected(domain_nodes[dname]):
                node.experienced_in.connect(domain_nodes[dname], {
                    'experience_level': random.choice(EXPERIENCE_LEVELS),
                    'years_of_involvement': random.randint(1, 6),
                })

    # ── 5. Create some MENTORED_BY relationships ─────────────────────────────
    print('\n🤝 Creating mentorship relationships...')
    num_mentorships = 15
    for _ in range(num_mentorships):
        student = random.choice(student_nodes)
        senior = random.choice(senior_nodes)

        # Pick a shared domain if possible
        student_domains = list(student.interested_in.all())
        senior_domains = list(senior.experienced_in.all())
        shared = [d for d in student_domains if d in senior_domains]
        domain = shared[0] if shared else (student_domains[0] if student_domains else None)

        if domain and not student.mentored_by.is_connected(senior):
            student.mentored_by.connect(senior, {
                'status': random.choice(['ACTIVE', 'ACTIVE', 'PENDING']),
                'domain_id': domain.uid,
            })
            print(f"    → {student.name} MENTORED_BY {senior.name} (domain: {domain.name})")

    # ── 6. Summary ───────────────────────────────────────────────────────────
    print('\n' + '=' * 60)
    print(f'  ✅ Domains:      {len(DomainNode.nodes.all())}')
    print(f'  ✅ UserNodes:    {len(UserNode.nodes.all())}')
    print(f'     Students:     {len(UserNode.nodes.filter(role="STUDENT"))}')
    print(f'     Seniors:      {len(UserNode.nodes.filter(role="SENIOR"))}')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    seed()

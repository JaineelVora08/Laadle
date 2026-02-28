"""
LLMSynthesizer — categorize_advice (Top-K Majority) Test Script
=================================================================
Tests the opinion-clustering and majority/minority detection logic
in LLMSynthesizer.categorize_advice().

Run with:
    python manage.py shell < test_llm_categorize.py

Prerequisites:
    - GEMINI_API_KEY in settings (live Gemini tests skip if not set)
"""
import sys
import os
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beacon.settings')
import django
django.setup()

from django.conf import settings

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
# Instantiate synthesizer
# ════════════════════════════════════════════════════
print("\n── LLMSynthesizer.categorize_advice ──")

try:
    from apps.ai_services.llm_synthesizer import LLMSynthesizer
    synth = LLMSynthesizer()
    test("LLMSynthesizer instantiation", True)
except Exception as e:
    test("LLMSynthesizer instantiation", False, str(e))
    print("FATAL: Cannot continue.")
    sys.exit(1)

# ════════════════════════════════════════════════════
# TEST GROUP 1: Edge cases — no Gemini required
# ════════════════════════════════════════════════════
print()
print("── Edge Cases (no LLM) ──")

# Empty advice list
result = synth.categorize_advice("Any question", [])
test("Empty advice list → groups = []",     result['groups'] == [])
test("Empty advice list → majority = None", result['majority_group'] is None)
test("Empty advice list → minority = []",   result['minority_groups'] == [])

# Single advice item — should never call Gemini
single_id = str(uuid.uuid4())
result = synth.categorize_advice("What is ML?", [
    {'senior_id': single_id, 'content': 'Learn Python first.', 'trust_score': 0.8},
])
test("Single item → 1 group",                     len(result['groups']) == 1)
test("Single item → majority_group not None",      result['majority_group'] is not None)
test("Single item → minority_groups = []",         result['minority_groups'] == [])
test("Single item → correct senior_id in group",   single_id in result['majority_group']['senior_ids'])
test("Single item → avg_trust correct",            abs(result['majority_group']['avg_trust'] - 0.8) < 0.001)
test("Single item → label is string",              isinstance(result['majority_group']['label'], str))

# ════════════════════════════════════════════════════
# TEST GROUP 2: avg_trust enrichment (offline, using fallback path)
# ════════════════════════════════════════════════════
print()
print("── avg_trust Enrichment ──")

# We drive the fallback path by monkeypatching generate_content to raise
import unittest.mock as mock

fallback_ids = [str(uuid.uuid4()) for _ in range(3)]
fallback_advice = [
    {'senior_id': fallback_ids[0], 'content': 'Use Python', 'trust_score': 0.9},
    {'senior_id': fallback_ids[1], 'content': 'Learn basics', 'trust_score': 0.6},
    {'senior_id': fallback_ids[2], 'content': 'Build projects', 'trust_score': 0.75},
]

with mock.patch.object(synth.client.models, 'generate_content', side_effect=Exception("API down")):
    fallback_result = synth.categorize_advice("How to learn coding?", fallback_advice)

# Fallback collapses everyone into 1 group
expected_avg = sum(a['trust_score'] for a in fallback_advice) / len(fallback_advice)
test("Fallback → 1 group returned",          len(fallback_result['groups']) == 1)
test("Fallback → majority_group set",        fallback_result['majority_group'] is not None)
test("Fallback → minority_groups empty",     fallback_result['minority_groups'] == [])
test("Fallback → avg_trust computed correctly",
     abs(fallback_result['majority_group']['avg_trust'] - expected_avg) < 0.001)
test("Fallback → all senior IDs present",
     set(fallback_ids) == set(fallback_result['majority_group']['senior_ids']))

# ════════════════════════════════════════════════════
# TEST GROUP 3: Majority sorting logic (pure Python, no LLM)
# ════════════════════════════════════════════════════
print()
print("── Majority Sorting Logic ──")

# Patch generate_content to return a fake grouping JSON
fake_senior_ids = [str(uuid.uuid4()) for _ in range(5)]
fake_advice = [
    {'senior_id': fake_senior_ids[0], 'content': 'A', 'trust_score': 0.9},
    {'senior_id': fake_senior_ids[1], 'content': 'A also', 'trust_score': 0.8},
    {'senior_id': fake_senior_ids[2], 'content': 'A too', 'trust_score': 0.7},
    {'senior_id': fake_senior_ids[3], 'content': 'B', 'trust_score': 0.95},
    {'senior_id': fake_senior_ids[4], 'content': 'B too', 'trust_score': 0.85},
]

import json
fake_gemini_response = mock.MagicMock()
fake_gemini_response.text = json.dumps({
    "groups": [
        {"label": "Approach B", "senior_ids": [fake_senior_ids[3], fake_senior_ids[4]]},
        {"label": "Approach A", "senior_ids": [fake_senior_ids[0], fake_senior_ids[1], fake_senior_ids[2]]},
    ]
})

with mock.patch.object(synth.client.models, 'generate_content', return_value=fake_gemini_response):
    sort_result = synth.categorize_advice("Question", fake_advice)

# Approach A has 3 members → should be majority
majority = sort_result['majority_group']
minority = sort_result['minority_groups']

test("Returned 2 groups",                      len(sort_result['groups']) == 2)
test("Majority has largest membership (3)",     len(majority['senior_ids']) == 3)
test("Majority label is 'Approach A'",          majority['label'] == 'Approach A')
test("Minority list has 1 entry",               len(minority) == 1)
test("Minority label is 'Approach B'",          minority[0]['label'] == 'Approach B')

# avg_trust for Approach A: (0.9 + 0.8 + 0.7) / 3 = 0.8
test("Majority avg_trust ~ 0.8",
     abs(majority['avg_trust'] - 0.8) < 0.001)
# avg_trust for Approach B: (0.95 + 0.85) / 2 = 0.9
test("Minority avg_trust ~ 0.9",
     abs(minority[0]['avg_trust'] - 0.9) < 0.001)

# ════════════════════════════════════════════════════
# TEST GROUP 4: Tie-breaking by avg_trust
# ════════════════════════════════════════════════════
print()
print("── Tie-breaking by avg_trust ──")

tie_ids = [str(uuid.uuid4()) for _ in range(4)]
tie_advice = [
    {'senior_id': tie_ids[0], 'content': 'X', 'trust_score': 0.9},
    {'senior_id': tie_ids[1], 'content': 'X', 'trust_score': 0.8},
    {'senior_id': tie_ids[2], 'content': 'Y', 'trust_score': 0.95},
    {'senior_id': tie_ids[3], 'content': 'Y', 'trust_score': 0.85},
]
# Both groups have 2 members; Group Y has higher avg_trust → should be majority
tie_response = mock.MagicMock()
tie_response.text = json.dumps({
    "groups": [
        {"label": "Group X", "senior_ids": [tie_ids[0], tie_ids[1]]},
        {"label": "Group Y", "senior_ids": [tie_ids[2], tie_ids[3]]},
    ]
})
with mock.patch.object(synth.client.models, 'generate_content', return_value=tie_response):
    tie_result = synth.categorize_advice("Tie question", tie_advice)

test("Tie: majority is Group Y (higher avg_trust)",
     tie_result['majority_group']['label'] == 'Group Y')
test("Tie: minority is Group X",
     tie_result['minority_groups'][0]['label'] == 'Group X')

# ════════════════════════════════════════════════════
# TEST GROUP 5: Live Gemini call (requires GEMINI_API_KEY)
# ════════════════════════════════════════════════════
print()
print("── Live Gemini categorize_advice ──")

if has_gemini:
    live_ids = [str(uuid.uuid4()) for _ in range(4)]
    live_advice = [
        {'senior_id': live_ids[0], 'content': 'Start with Python basics and practice loops.',
         'trust_score': 0.85},
        {'senior_id': live_ids[1], 'content': 'Learn Python syntax: variables, loops, functions.',
         'trust_score': 0.80},
        {'senior_id': live_ids[2], 'content': 'Jump straight into building projects; learn by doing.',
         'trust_score': 0.75},
        {'senior_id': live_ids[3], 'content': 'Skip theory, just build real apps from day one.',
         'trust_score': 0.70},
    ]
    try:
        live_result = synth.categorize_advice("How should I start learning Python?", live_advice)
        test("Live: returns dict with groups key",        'groups' in live_result)
        test("Live: groups is a list",                   isinstance(live_result['groups'], list))
        test("Live: at least 1 group returned",          len(live_result['groups']) >= 1)
        test("Live: majority_group is not None",         live_result['majority_group'] is not None)
        test("Live: minority_groups is a list",          isinstance(live_result['minority_groups'], list))
        test("Live: all senior IDs accounted for",
             set(live_ids) == {sid for g in live_result['groups'] for sid in g['senior_ids']})
        test("Live: majority has label (string)",        isinstance(live_result['majority_group']['label'], str))
        test("Live: majority avg_trust is float",        isinstance(live_result['majority_group']['avg_trust'], float))
        test("Live: majority has >= 1 member",           len(live_result['majority_group']['senior_ids']) >= 1)
    except Exception as e:
        test("Live categorize_advice()", False, str(e))
else:
    skip("Live categorize_advice()", "GEMINI_API_KEY not set")

# ════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════
total = passed + failed
print()
print("=" * 50)
if failed == 0:
    print(f"🎉 ALL {total} TESTS PASSED! ({skipped} skipped)")
else:
    print(f"Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")
print("=" * 50)

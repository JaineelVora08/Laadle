"""
AI Services Test Script
========================
Tests: EmbeddingGenerator, RAGEngine, LLMSynthesizer, ConflictConsensusEngine

Run with:
    python manage.py shell < test_ai_services.py

Prerequisites:
    - e5-base-v2 model will be downloaded on first run (~440MB)
    - Pinecone API key in settings (optional — tests gracefully skip if not set)
    - GEMINI_API_KEY in settings (optional — Gemini tests skip if not set)
"""
import sys
import os

# Ensure Django settings are loaded
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


# ═══════════════════════════════════════════════
# TEST GROUP 1: EmbeddingGenerator (Local e5-base-v2)
# ═══════════════════════════════════════════════
print("\n── EmbeddingGenerator ──")

try:
    from apps.ai_services.embedding_generator import EmbeddingGenerator
    gen = EmbeddingGenerator()
    test("EmbeddingGenerator instantiation", True)
except Exception as e:
    test("EmbeddingGenerator instantiation", False, str(e))
    print("FATAL: Cannot proceed without EmbeddingGenerator")
    sys.exit(1)

# Test generate (passage embedding)
emb = gen.generate("Machine learning is a subfield of AI")
test("generate() returns list", isinstance(emb, list))
test("generate() returns 768-dim vector", len(emb) == 768)
test("generate() returns floats", all(isinstance(x, float) for x in emb))
test("generate() returns non-zero vector", any(x != 0.0 for x in emb))

# Test generate_query_embedding
q_emb = gen.generate_query_embedding("What is machine learning?")
test("generate_query_embedding() returns list", isinstance(q_emb, list))
test("generate_query_embedding() returns 768-dim", len(q_emb) == 768)

# Test that query and passage embeddings are different
# (due to different prefixes: "query: " vs "passage: ")
test("query vs passage embeddings differ", emb != q_emb)

# Test similarity: similar texts should have higher similarity
import numpy as np
emb1 = gen.generate("Python programming language")
emb2 = gen.generate("Python coding and software development")
emb3 = gen.generate("Ancient Egyptian history and pyramids")

sim_similar = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
sim_different = np.dot(emb1, emb3) / (np.linalg.norm(emb1) * np.linalg.norm(emb3))
test(f"Similar texts have higher similarity ({sim_similar:.3f} > {sim_different:.3f})",
     sim_similar > sim_different)

# Test Pinecone integration
if gen.index is not None:
    test("Pinecone index connected", True)
    store_result = gen.store("test-vec-001", emb1, {"domain_name": "test", "type": "test"})
    test("store() returns True", store_result is True)

    similar = gen.query_similar(emb1, top_k=1)
    test("query_similar() returns list", isinstance(similar, list))
    if similar:
        test("query_similar() returns dict with id/score/metadata",
             all(k in similar[0] for k in ['id', 'score', 'metadata']))

    # Cleanup test vector
    try:
        gen.index.delete(ids=["test-vec-001"])
        print("  (cleaned up test vector)")
    except:
        pass
else:
    skip("Pinecone store()", "PINECONE_API_KEY not set")
    skip("Pinecone query_similar()", "PINECONE_API_KEY not set")

print()

# ═══════════════════════════════════════════════
# TEST GROUP 2: RAGEngine
# ═══════════════════════════════════════════════
print("── RAGEngine ──")

has_gemini = bool(getattr(settings, 'GEMINI_API_KEY', ''))

try:
    from apps.ai_services.rag_engine import RAGEngine
    rag = RAGEngine()
    test("RAGEngine instantiation", True)
except Exception as e:
    test("RAGEngine instantiation", False, str(e))
    rag = None

if rag:
    # Test retrieve_similar_cases (will return empty if Pinecone has no data)
    test_emb = gen.generate_query_embedding("How do I learn machine learning?")
    cases = rag.retrieve_similar_cases(test_emb, "00000000-0000-0000-0000-000000000000")
    test("retrieve_similar_cases() returns list", isinstance(cases, list))

    # Test generate_provisional_response (needs Gemini)
    if has_gemini:
        try:
            response = rag.generate_provisional_response(
                "How do I start with ML?",
                [{'query_text': 'What is ML?', 'advice_text': 'Start with courses', 'trust_score': 0.8}],
                [{'advice_text': 'Take Andrew Ng course', 'trust_score': 0.9}]
            )
            test("generate_provisional_response() returns string", isinstance(response, str))
            test("generate_provisional_response() non-empty", len(response) > 0)
        except Exception as e:
            test("generate_provisional_response()", False, str(e))
    else:
        skip("generate_provisional_response()", "GEMINI_API_KEY not set")

print()

# ═══════════════════════════════════════════════
# TEST GROUP 3: LLMSynthesizer
# ═══════════════════════════════════════════════
print("── LLMSynthesizer ──")

try:
    from apps.ai_services.llm_synthesizer import LLMSynthesizer
    synth = LLMSynthesizer()
    test("LLMSynthesizer instantiation", True)
except Exception as e:
    test("LLMSynthesizer instantiation", False, str(e))
    synth = None

if synth:
    # Test compute_weight
    w = synth.compute_weight(0.8, 0.9)
    test("compute_weight(0.8, 0.9) = 0.72", abs(w - 0.72) < 0.001)

    # Test empty advice list
    result = synth.synthesize("Test question", [])
    test("synthesize() handles empty list",
         result['final_answer'] == 'No senior responses received yet.')
    test("synthesize() empty returns empty lists",
         result['agreements'] == [] and result['disagreements'] == [])

    # Test synthesize with real data (needs Gemini)
    if has_gemini:
        try:
            result = synth.synthesize(
                "How to learn Python?",
                [
                    {'content': 'Start with basics, learn loops and functions',
                     'senior_id': 'sr1', 'trust_score': 0.9, 'similarity_score': 0.8},
                    {'content': 'Build projects, practice on LeetCode',
                     'senior_id': 'sr2', 'trust_score': 0.7, 'similarity_score': 0.6},
                ]
            )
            test("synthesize() returns dict with final_answer", 'final_answer' in result)
            test("synthesize() returns agreements list", isinstance(result.get('agreements'), list))
            test("synthesize() returns disagreements list", isinstance(result.get('disagreements'), list))
        except Exception as e:
            test("synthesize() with advice", False, str(e))

        # Test follow-up generation
        try:
            followups = synth.generate_followup_questions("How to learn Python?", "test-domain")
            test("generate_followup_questions() returns list", isinstance(followups, list))
            test("generate_followup_questions() returns <= 3 items", len(followups) <= 3)
        except Exception as e:
            test("generate_followup_questions()", False, str(e))
    else:
        skip("synthesize() with real data", "GEMINI_API_KEY not set")
        skip("generate_followup_questions()", "GEMINI_API_KEY not set")

print()

# ═══════════════════════════════════════════════
# TEST GROUP 4: ConflictConsensusEngine
# ═══════════════════════════════════════════════
print("── ConflictConsensusEngine ──")

try:
    from apps.ai_services.conflict_consensus_engine import ConflictConsensusEngine
    conflict_eng = ConflictConsensusEngine()
    test("ConflictConsensusEngine instantiation", True)
except Exception as e:
    test("ConflictConsensusEngine instantiation", False, str(e))
    conflict_eng = None

if conflict_eng:
    # Test _cosine_similarity
    sim = ConflictConsensusEngine._cosine_similarity([1, 0, 0], [1, 0, 0])
    test("_cosine_similarity identical = 1.0", abs(sim - 1.0) < 0.001)

    sim = ConflictConsensusEngine._cosine_similarity([1, 0, 0], [0, 1, 0])
    test("_cosine_similarity orthogonal = 0.0", abs(sim) < 0.001)

    sim = ConflictConsensusEngine._cosine_similarity([1, 0, 0], [-1, 0, 0])
    test("_cosine_similarity opposite = -1.0", abs(sim - (-1.0)) < 0.001)

    sim = ConflictConsensusEngine._cosine_similarity([0, 0, 0], [1, 0, 0])
    test("_cosine_similarity zero vector = 0.0", sim == 0.0)

    # Test detect_anomaly with empty history
    test("detect_anomaly() empty history = False",
         conflict_eng.detect_anomaly("some advice", []) == False)

    # Test detect_anomaly with similar advice
    anomaly = conflict_eng.detect_anomaly(
        "Learn Python basics first, start with loops",
        ["Study Python fundamentals, begin with loops and functions"]
    )
    test(f"detect_anomaly() similar advice = {anomaly} (expected False)", anomaly == False)

    # Test detect_anomaly with completely unrelated advice (anomaly = topic drift)
    # NOTE: E5 measures topical similarity, NOT semantic negation.
    # "rain tomorrow" vs "no rain tomorrow" are same topic → high similarity.
    # True anomalies are when someone gives advice on a totally different subject.
    anomaly = conflict_eng.detect_anomaly(
        "You are a bad person",
        [
            "Start with Python basics, learn loops and functions first",
            "Build small projects to practice your coding skills",
        ]
    )
    test(f"detect_anomaly() unrelated advice = {anomaly} (expected True)", anomaly == True)

    # Test ANOMALY_THRESHOLD value
    test("ANOMALY_THRESHOLD is 0.75", ConflictConsensusEngine.ANOMALY_THRESHOLD == 0.75)

print()

# ═══════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════
total = passed + failed
print("=" * 50)
if failed == 0:
    print(f"🎉 ALL {total} TESTS PASSED! ({skipped} skipped)")
else:
    print(f"Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")
print("=" * 50)

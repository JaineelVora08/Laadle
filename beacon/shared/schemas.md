# BEACON — Shared JSON Schemas (API Contracts)

All 4 modules must match these shapes exactly.

---

## AuthTokenResponse
```json
{
  "access": "string",
  "refresh": "string",
  "user_id": "string (UUID)",
  "role": "string (STUDENT | SENIOR)"
}
```

## UserProfileResponse
```json
{
  "id": "string (UUID)",
  "name": "string",
  "email": "string",
  "role": "string (STUDENT | SENIOR)",
  "availability": "boolean",
  "trust_score": "float",
  "current_level": "string",
  "active_load": "integer",
  "low_energy_mode": "boolean | null",
  "momentum_score": "float | null",
  "consistency_score": "float | null",
  "alignment_score": "float | null",
  "follow_through_rate": "float | null",
  "achievements": [
    {
      "id": "string (UUID)",
      "title": "string",
      "proof_url": "string",
      "verified": "boolean",
      "created_at": "string (ISO 8601)"
    }
  ]
}
```

## DomainLinkResponse
```json
{
  "domain_id": "string (UUID)",
  "name": "string",
  "type": "string",
  "priority": "integer",
  "current_level": "string",
  "embedding_ref": "string (Pinecone ID)",
  "popularity_score": "float"
}
```

## MentorMatchRequest
```json
{
  "student_id": "string (UUID)",
  "domain_id": "string (UUID)",
  "priority": "integer"
}
```

## MentorMatchResponse
```json
{
  "senior_id": "string (UUID)",
  "name": "string",
  "trust_score": "float",
  "domain": "string",
  "experience_level": "string",
  "availability": "boolean",
  "active_load": "integer"
}
```

## PeerMatchResponse
```json
{
  "student_id": "string (UUID)",
  "name": "string",
  "domain": "string",
  "current_level": "string",
  "priority": "integer"
}
```

## TrustUpdateRequest
```json
{
  "senior_id": "string (UUID)",
  "student_feedback_score": "float",
  "consistency_score": "float",
  "alignment_score": "float",
  "follow_through_rate": "float",
  "achievement_weight": "float"
}
```

## QuerySubmitRequest
```json
{
  "student_id": "string (UUID)",
  "domain_id": "string (UUID)",
  "content": "string"
}
```

## QuerySubmitResponse
```json
{
  "query_id": "string (UUID)",
  "status": "string (PENDING | IN_PROGRESS | RESOLVED)",
  "provisional_answer": "string",
  "follow_up_questions": ["string"],
  "matched_seniors": ["string (UUID)"],
  "timestamp": "string (ISO 8601)"
}
```

## SeniorResponseRequest
```json
{
  "senior_id": "string (UUID)",
  "advice_content": "string",
  "answered_followups": [
    {
      "question": "string",
      "answer": "string"
    }
  ]
}
```

## FinalAdviceResponse
```json
{
  "query_id": "string (UUID)",
  "final_answer": "string",
  "agreements": ["string"],
  "disagreements": ["string"],
  "conflict_detected": "boolean",
  "conflict_details": "string | null",
  "contributing_seniors": [
    {
      "senior_id": "string (UUID)",
      "trust_score": "float",
      "weight": "float"
    }
  ]
}
```

## QueryStatusResponse
```json
{
  "query_id": "string (UUID)",
  "status": "string (PENDING | IN_PROGRESS | RESOLVED)",
  "provisional_answer": "string | null",
  "final_answer": "string | null",
  "follow_up_questions": ["string"],
  "conflict_detected": "boolean"
}
```

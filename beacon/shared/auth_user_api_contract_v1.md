# BEACON Auth + User Layer API Contract (Frozen v1)

Status: Frozen for implementation phase  
Date: 2026-02-28  
Scope: Auth service + User profile service only

This document is the single source of truth for request/response shapes for user/auth integration. Backend and frontend must follow this exactly.

---

## 1) Global Rules

- Base URL prefix: `/api`
- Content type: `application/json`
- Auth header for protected endpoints: `Authorization: Bearer <access_token>`
- IDs are UUID strings.
- Role enum: `STUDENT | SENIOR`
- Timestamp format: ISO 8601 UTC string.

### Error Envelope (all endpoints)

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

---

## 2) Shared Objects

### AuthTokenResponse

```json
{
  "access": "string",
  "refresh": "string",
  "user_id": "string (UUID)",
  "role": "string (STUDENT | SENIOR)"
}
```

### AchievementObject

```json
{
  "id": "string (UUID)",
  "title": "string",
  "proof_url": "string",
  "verified": "boolean",
  "created_at": "string (ISO 8601)"
}
```

### UserProfileResponse

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

---

## 3) Public Auth API Contracts

### POST `/api/auth/register/`

Request:

```json
{
  "name": "string",
  "email": "string",
  "password": "string",
  "role": "STUDENT | SENIOR"
}
```

Success:
- `201 Created`
- Body: `AuthTokenResponse`

Errors:
- `400 Bad Request` validation failure
- `409 Conflict` email already exists

### POST `/api/auth/login/`

Request:

```json
{
  "email": "string",
  "password": "string"
}
```

Success:
- `200 OK`
- Body: `AuthTokenResponse`

Errors:
- `400 Bad Request` invalid payload
- `401 Unauthorized` invalid credentials

### POST `/api/auth/google/login/`

Request:

```json
{
  "id_token": "string",
  "role": "STUDENT | SENIOR (optional, default STUDENT)",
  "current_level": "string (optional)"
}
```

Success:
- `200 OK`
- Body: `AuthTokenResponse`

Rules:
- Google token must be valid for configured backend Google OAuth client ID.
- Email must be verified by Google.
- Only `@iitj.ac.in` domain is allowed.

Errors:
- `400 Bad Request` invalid token/payload/domain
- `401 Unauthorized` token verification failure

### POST `/api/auth/token/refresh/`

Request:

```json
{
  "refresh": "string"
}
```

Success:
- `200 OK`
- Body:

```json
{
  "access": "string",
  "refresh": "string"
}
```

Notes:
- Refresh rotation is enabled.
- Previous refresh token is blacklisted on successful refresh.

Errors:
- `401 Unauthorized` invalid/expired/blacklisted refresh token

### POST `/api/auth/logout/`

Request:

```json
{
  "refresh": "string"
}
```

Success:
- `200 OK`
- Body:

```json
{
  "message": "Logged out successfully"
}
```

Notes:
- Provided refresh token is blacklisted.

Errors:
- `400 Bad Request` refresh missing or malformed
- `401 Unauthorized` token invalid

---

## 4) Public User Profile API Contracts

### GET `/api/profile/{user_id}/`

Auth: Required

Success:
- `200 OK`
- Body: `UserProfileResponse`

Errors:
- `401 Unauthorized` missing/invalid access token
- `403 Forbidden` trying to access a different user without permission
- `404 Not Found` user/profile not found

### PATCH `/api/profile/{user_id}/update/`

Auth: Required

Request (partial update allowed):

```json
{
  "name": "string",
  "availability": true,
  "current_level": "string",
  "low_energy_mode": false,
  "momentum_score": 0.0,
  "consistency_score": 0.0,
  "alignment_score": 0.0,
  "follow_through_rate": 0.0
}
```

Success:
- `200 OK`
- Body: `UserProfileResponse`

Errors:
- `400 Bad Request` validation error
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

### GET `/api/profile/{user_id}/achievements/`

Auth: Required

Success:
- `200 OK`
- Body:

```json
{
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

Errors:
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

### POST `/api/profile/{user_id}/achievements/`

Auth: Required

Request:

```json
{
  "title": "string",
  "proof_url": "string"
}
```

Success:
- `201 Created`
- Body: `AchievementObject`

Errors:
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

---

## 5) Internal API Contracts (for service-to-service calls)

Auth: Header `X-Internal-Secret: <INTERNAL_SECRET>` required on all internal endpoints.

### GET `/internal/users/{user_id}/`

Success:
- `200 OK`

```json
{
  "id": "string (UUID)",
  "email": "string",
  "name": "string",
  "role": "STUDENT | SENIOR",
  "availability": "boolean",
  "active_load": "integer",
  "trust_score": "float"
}
```

Errors:
- `401 Unauthorized` missing/invalid internal secret
- `404 Not Found`

### POST `/internal/users/{senior_id}/increment-load/`

Request:

```json
{
  "delta": 1
}
```

Success:
- `200 OK`

```json
{
  "senior_id": "string (UUID)",
  "active_load": "integer"
}
```

Errors:
- `400 Bad Request` invalid delta
- `401 Unauthorized`
- `404 Not Found`

### GET `/internal/profile/{user_id}/`

Success:
- `200 OK`
- Body: `UserProfileResponse`

Errors:
- `401 Unauthorized`
- `404 Not Found`

---

## 6) Compatibility Rules

- Any change to field names, enums, status codes, or required/optional behavior must create a new versioned contract file (for example `auth_user_api_contract_v2.md`) before implementation.
- Frontend integration and backend implementation must both reference this v1 file during development and QA.
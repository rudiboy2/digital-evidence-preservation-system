# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/api/docs`

---

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require a Bearer JWT token:

```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "officer@department.gov",
  "full_name": "Jane Smith",
  "password": "SecurePassword123!",
  "badge_number": "B-1042",
  "department": "Digital Forensics",
  "role_name": "officer"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "email": "officer@department.gov",
  "full_name": "Jane Smith",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00"
}
```

---

### POST /auth/login
Authenticate and receive tokens.

**Request Body (form-urlencoded):**
```
username=officer@department.gov&password=SecurePassword123!
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

### POST /auth/refresh
Refresh an expired access token.

```json
{ "refresh_token": "eyJ..." }
```

---

### GET /auth/me
Return the current user's profile.

---

## Cases Endpoints

### POST /cases/
Create a new investigation case. Requires `investigator` or `admin` role.

```json
{
  "title": "Digital Fraud Q3 2024",
  "description": "Investigation of suspected wire fraud.",
  "priority": "high",
  "jurisdiction": "Federal"
}
```

---

### GET /cases/
List cases (paginated). Non-admins only see cases they are assigned to.

**Query params:** `page`, `page_size`, `status`

---

### GET /cases/{case_id}
Get details for a specific case.

---

### PATCH /cases/{case_id}
Update case metadata. Requires `investigator` or `admin`.

---

### POST /cases/{case_id}/close
Close a case. Requires `admin`.

---

### POST /cases/{case_id}/assign/{user_id}
Assign a user to a case. Requires `admin`.

---

## Evidence Endpoints

### POST /evidence/upload
Upload an evidence file.

**Query params:** `case_id` (UUID), `description` (string)

**Body:** `multipart/form-data` with `file` field.

**Response 201:**
```json
{
  "id": "uuid",
  "case_id": "uuid",
  "uploaded_by": "uuid",
  "file_name": "surveillance_footage.mp4",
  "file_size": 104857600,
  "mime_type": "video/mp4",
  "evidence_type": "video",
  "sha256_hash": "a3f2...c9d1",
  "ipfs_cid": "QmXoypiz...",
  "blockchain_tx_hash": "0xabc123...",
  "blockchain_block_number": 14302,
  "description": "CCTV footage from location A",
  "status": "verified",
  "created_at": "2024-01-15T11:30:00"
}
```

---

### GET /evidence/{evidence_id}
Retrieve evidence metadata by ID.

---

### GET /evidence/case/{case_id}
List all evidence for a case (paginated).

---

### POST /evidence/{evidence_id}/verify
Verify file integrity against the blockchain.

**Response:**
```json
{
  "evidence_id": "uuid",
  "is_valid": true,
  "db_hash": "a3f2...c9d1",
  "computed_hash": "a3f2...c9d1",
  "blockchain_hash": "a3f2...c9d1",
  "blockchain_tx_hash": "0xabc123...",
  "status": "verified",
  "message": "Evidence integrity verified. Hash matches blockchain record."
}
```

---

### GET /evidence/{evidence_id}/custody-chain
Return the full chain-of-custody log.

```json
{
  "evidence_id": "uuid",
  "custody_chain": [
    {
      "id": "uuid",
      "action": "uploaded",
      "performed_by": "uuid",
      "notes": "Initial upload: surveillance_footage.mp4",
      "blockchain_tx_hash": "0xdef456...",
      "timestamp": "2024-01-15T11:30:00"
    },
    {
      "id": "uuid",
      "action": "transferred",
      "performed_by": "uuid",
      "notes": "Transferred to lead investigator",
      "blockchain_tx_hash": "0xghi789...",
      "timestamp": "2024-01-16T09:00:00"
    }
  ]
}
```

---

### DELETE /evidence/{evidence_id}
Soft-delete evidence. Requires `admin`. Blockchain record is preserved.

---

## Error Responses

All errors follow the RFC 7807 format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid JWT token |
| 403 | Insufficient role/permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate email) |
| 413 | File too large |
| 422 | Unprocessable entity (schema validation) |
| 500 | Internal server error |

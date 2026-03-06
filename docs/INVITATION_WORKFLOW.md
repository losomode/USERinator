# Invitation Workflow

## Overview

USERinator implements an approval-based invitation workflow for adding users to companies. Users request to join a company, company admins review the request, and on approval the user's profile is created.

## Workflow States

```
PENDING ──→ APPROVED ──→ (UserProfile created)
   │
   ├──→ REJECTED
   │
   └──→ EXPIRED (auto, after 7 days)
```

## Sequence Diagram

```
User                    USERinator                    AUTHinator
 │                          │                             │
 │  POST /api/invitations/  │                             │
 │  {email, company, role}  │                             │
 │─────────────────────────>│                             │
 │                          │  Create invitation          │
 │                          │  status=PENDING             │
 │                          │  expires_at=now+7d          │
 │  201 Created             │                             │
 │<─────────────────────────│                             │
 │                          │  Send email to company      │
 │                          │  admins (notification)      │
 │                          │                             │
 │                          │                             │
Admin                   USERinator                    AUTHinator
 │                          │                             │
 │  GET /api/invitations/   │                             │
 │  ?status=PENDING         │                             │
 │─────────────────────────>│                             │
 │  200 [invitations]       │                             │
 │<─────────────────────────│                             │
 │                          │                             │
 │  POST /api/invitations/  │                             │
 │  {id}/approve/           │                             │
 │─────────────────────────>│                             │
 │                          │  Update status=APPROVED     │
 │                          │  Set reviewed_at, reviewed_by│
 │                          │                             │
 │                          │  POST /api/auth/create-user/│
 │                          │────────────────────────────>│
 │                          │  {email, role, company}     │
 │                          │                             │
 │                          │  201 {user_id}              │
 │                          │<────────────────────────────│
 │                          │                             │
 │                          │  Create UserProfile         │
 │                          │  {user_id, email, role,     │
 │                          │   company}                  │
 │                          │                             │
 │  200 {invitation}        │                             │
 │<─────────────────────────│                             │
 │                          │  Send approval email to user│
```

## API Reference

### Create Invitation (Request to Join)

```http
POST /api/invitations/
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "company": 1,
  "requested_role": 3
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "newuser@example.com",
  "company": 1,
  "requested_role": 3,
  "status": "PENDING",
  "requested_at": "2026-03-06T00:00:00Z",
  "expires_at": "2026-03-13T00:00:00Z"
}
```

**Validation:**
- Duplicate pending invitation for same email+company is rejected (400)
- Email must be valid
- Company and role must exist

### List Invitations (Admin)

```http
GET /api/invitations/?status=PENDING
Authorization: Bearer <token>
```

Requires `role_level >= 30` (IsCompanyAdmin). Results are company-scoped.

### Approve Invitation (Admin)

```http
POST /api/invitations/{id}/approve/
Authorization: Bearer <token>
Content-Type: application/json

{
  "review_notes": "Welcome aboard!"
}
```

**Response (200):** Updated invitation with `status: "APPROVED"`.

**Business Logic:**
1. Validates invitation is PENDING and not expired
2. Updates status to APPROVED
3. Calls AUTHinator to create user account (if configured)
4. Creates UserProfile in USERinator
5. Sends approval notification email to user

### Reject Invitation (Admin)

```http
POST /api/invitations/{id}/reject/
Authorization: Bearer <token>
Content-Type: application/json

{
  "review_notes": "Position filled."
}
```

**Response (200):** Updated invitation with `status: "REJECTED"`.

### Invitation Expiration

Invitations expire after 7 days. The `expire_invitations` management command marks expired invitations:

```bash
task backend:manage -- expire_invitations
```

This can be scheduled via cron for automatic cleanup.

## Permissions

| Action | Required Role |
|--------|--------------|
| Create invitation | Any authenticated user |
| List invitations | Company Admin (role_level ≥ 30) |
| View invitation detail | Any authenticated user |
| Approve invitation | Company Admin (role_level ≥ 30) |
| Reject invitation | Company Admin (role_level ≥ 30) |

## Error Handling

- **Duplicate invitation:** 400 — "A pending invitation already exists for this email and company."
- **Already reviewed:** 400 — "Invitation is APPROVED, not PENDING."
- **Expired:** 400 — "Invitation has expired." (status auto-updated to EXPIRED)
- **Not found:** 404 — "Invitation not found."
- **AUTHinator unavailable:** Approval succeeds but UserProfile creation is deferred. Logged as warning.

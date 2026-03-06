# AUTHinator ↔ USERinator Integration

## Overview

USERinator is the **source of truth** for user profiles, companies, and roles. AUTHinator handles authentication (credentials, JWT tokens, MFA, SSO). During login, AUTHinator queries USERinator for the user's role and includes it in the JWT token.

## Role Query API

### Endpoint

```
GET /api/users/{user_id}/role/
```

### Authentication

Requires a valid Bearer token (service-to-service or admin).

### Response

```json
{
  "user_id": 1,
  "role_name": "ADMIN",
  "role_level": 100,
  "company": 1
}
```

### Response Codes

- `200 OK` — Role data returned
- `401 Unauthorized` — Invalid or missing token
- `404 Not Found` — User not found or inactive

### Performance

- Target: <50ms p95 response time
- Single database query with no joins
- AUTHinator should cache responses (recommended TTL: 5 minutes)

## JWT Token Changes

### Current (AUTHinator-only)

```json
{
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "ADMIN"
}
```

### Updated (with USERinator role data)

```json
{
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "ADMIN",
  "role_level": 100,
  "company_id": 1
}
```

### New Claims

- `role_level` (integer): Numeric role level from USERinator (ADMIN=100, MANAGER=30, MEMBER=10)
- `company_id` (integer): User's company ID from USERinator

## Token Invalidation on Role Change

When a user's role is changed in USERinator:

1. USERinator updates the `role_name` and `role_level` on the UserProfile
2. The change takes effect on the **next token refresh** (existing tokens remain valid until expiry)
3. For immediate invalidation, AUTHinator should implement a token blacklist or short token lifetimes

### Recommended Approach

- Set `ACCESS_TOKEN_LIFETIME` to 15-30 minutes
- On role change, optionally call AUTHinator's `/api/auth/invalidate-user/{user_id}/` endpoint (if implemented)
- AUTHinator re-queries USERinator on each token refresh

## AUTHinator Login Flow (Updated)

```
User → AUTHinator: POST /api/auth/login/ {username, password}
AUTHinator → AUTHinator: Validate credentials
AUTHinator → USERinator: GET /api/users/{user_id}/role/
USERinator → AUTHinator: {role_name, role_level, company_id}
AUTHinator → AUTHinator: Generate JWT with role_level + company_id
AUTHinator → User: {access_token, refresh_token}
```

## Migration Checklist

### Phase 1: Deploy USERinator
- [ ] Deploy USERinator service on port 8004
- [ ] Run `create_default_roles` to seed ADMIN/MANAGER/MEMBER roles
- [ ] Run data migration from AUTHinator (`migrate_from_authinator`)
- [ ] Verify all users have UserProfile records

### Phase 2: Update AUTHinator
- [ ] Add USERinator API client to AUTHinator
- [ ] Modify login flow to query `/api/users/{id}/role/`
- [ ] Add `role_level` and `company_id` claims to JWT
- [ ] Add fallback: if USERinator unavailable, use cached role or default to MEMBER
- [ ] Test with both old and new token formats

### Phase 3: Update Other Services
- [ ] Update RMAinator to read `role_level` from JWT
- [ ] Update FULFILinator to read `role_level` from JWT
- [ ] Remove hardcoded role checks, use numeric level comparisons

### Phase 4: Cleanup
- [ ] Remove role management from AUTHinator admin
- [ ] Update AUTHinator docs to reference USERinator for roles
- [ ] Monitor logs for any role query failures

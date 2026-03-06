# Cross-Service Coordination: Integrate USERinator into the Inator Platform

## Problem Statement
USERinator (port 8004) is built but isolated. The platform currently routes `/api/users/*` to AUTHinator (port 8001), and all services use AUTHinator's simple `ADMIN`/`USER` role for permissions. We need to:
1. Re-route `/api/users/*` to USERinator
2. Enrich JWT tokens with `role_level` from USERinator
3. Update RMAinator + FULFILinator to use the richer role system
4. Add USERinator to the unified frontend

## Steps
1. AUTHinator — Move approval endpoints from `/api/users/` to `/api/auth/users/`
2. AUTHinator — Enrich JWT with `role_level` via USERinator client + `create_enriched_tokens()` helper
3. Caddyfile — Route `/api/users/*` to :8004, add company/role/invitation routes
4. RMAinator — Use `role_level` from enriched auth, add USERinator profile client
5. FULFILinator — Mirror RMAinator changes
6. Unified Frontend — Add `users` module, update AuthProvider
7. Tests & Verification — `task check` across all services

## Date
2026-03-06

# Migration Guide: AUTHinator → USERinator

## Overview

This guide covers migrating user profile and role data from AUTHinator to USERinator, making USERinator the authoritative source for user profiles, companies, and roles.

## Pre-Migration Steps

1. **Deploy USERinator** (see `DEPLOYMENT.md`)
2. **Create default roles:**
   ```bash
   task backend:manage -- create_default_roles
   ```
3. **Verify AUTHinator API is accessible:**
   ```bash
   curl http://localhost:8001/api/auth/users/
   ```

## Migration Process

### Step 1: Dry Run

Preview what will be migrated without making changes:

```bash
task backend:manage -- migrate_from_authinator --dry-run
```

Review the output. Each user will show the target company and role mapping.

### Step 2: Execute Migration

```bash
task backend:manage -- migrate_from_authinator
```

Options:
- `--default-company="Company Name"` — Company for users without one (default: "Default Company")

### Step 3: Verify Data Integrity

```bash
task backend:manage -- verify_migration
```

This checks:
- User profile counts (total, active, inactive)
- Company counts
- Role distribution
- Orphan roles (users with roles not in Role table)
- Empty companies (active companies with no users)
- Duplicate emails

### Step 4: Update AUTHinator

After migration, AUTHinator needs to:
1. Query USERinator `/api/users/{id}/role/` during login
2. Include `role_level` claim in JWT tokens
3. Keep username/email in its own database (stub pattern)

See `docs/AUTHINATOR_INTEGRATION.md` for details.

### Step 5: Update Other Services

- **RMAinator**: Add USERinator API calls for profiles, cache with 5min TTL
- **FULFILinator**: Same as RMAinator

## Role Mapping

| AUTHinator Role | USERinator Role | Level |
|---|---|---|
| ADMIN | ADMIN | 100 |
| MANAGER | MANAGER | 30 |
| MEMBER | MEMBER | 10 |
| USER | MEMBER | 10 |

## Rollback Procedure

1. Stop USERinator
2. Revert AUTHinator to not query USERinator
3. Other services continue using AUTHinator directly
4. No data loss — AUTHinator retains all auth data

## Testing Checklist

- [ ] Dry run completes without errors
- [ ] Migration creates correct number of profiles
- [ ] `verify_migration` shows no orphans or duplicates
- [ ] Health check returns `healthy`
- [ ] Users can log in via AUTHinator
- [ ] Profile data appears correctly in USERinator frontend
- [ ] Other services can query USERinator API

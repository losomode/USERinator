# USERinator Architecture

## System Context

```
                    ┌─────────────────┐
                    │    Caddy :8080   │
                    │ (Unified Gateway)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                     │
        ▼                    ▼                     ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ AUTHinator    │  │  USERinator     │  │ RMAinator /      │
│ :8001         │  │  :8004          │  │ FULFILinator     │
│               │  │                 │  │ :8002 / :8003    │
│ • Auth/Login  │  │ • User Profiles │  │                  │
│ • JWT Tokens  │◄─┤ • Companies     │──►│ • Reads profiles │
│ • MFA / SSO   │  │ • Roles         │  │ • Checks roles   │
│ • Credentials │  │ • Preferences   │  │ • Caches (5min)  │
└───────────────┘  │ • Invitations   │  └──────────────────┘
                   └─────────────────┘
```

## Authentication Flow

```
Browser → Caddy → AUTHinator (login) → JWT token
       → Caddy → USERinator (Bearer token)
                → Validate with AUTHinator /api/auth/me/
                → Get/create local User stub
                → Attach role_level, company_id
                → Return profile data
```

## Data Model

```
┌──────────────┐     ┌────────────────┐
│   Company    │     │     Role       │
├──────────────┤     ├────────────────┤
│ name         │     │ role_name      │
│ industry     │     │ role_level     │
│ company_size │     │ description    │
│ tags (JSON)  │     │ is_system_role │
│ custom_fields│     └────────────────┘
│ account_status│           │
└──────┬───────┘           │
       │ 1:N               │
       ▼                   │
┌──────────────────┐       │
│   UserProfile    │       │
├──────────────────┤       │
│ user_id (PK)     │       │
│ username         │       │
│ email            │       │
│ display_name     │       │
│ role_name ───────┼───────┘
│ role_level       │
│ timezone         │
│ language         │
│ is_active        │
└──────────────────┘
       │ 1:N
       ▼
┌──────────────────┐
│ UserInvitation   │
├──────────────────┤
│ email            │
│ company (FK)     │
│ requested_role   │
│ status           │
│ expires_at       │
└──────────────────┘
```

## Django Apps

| App | Responsibility |
|---|---|
| `core` | Authentication, permissions, management commands |
| `users` | User profiles, preferences, health check |
| `companies` | Company CRUD, company-scoped queries |
| `roles` | Role definitions, assignment validation |
| `invitations` | Invitation workflow (request → review → approve/reject) |

## Permission Model

Permissions use numeric role levels for comparison:

- **Platform Admin** (≥100): Full access to all resources
- **Company Admin** (≥30): Manage users/resources within own company
- **Member** (≥10): View own company, edit own profile

Company scoping ensures users only see data within their own company, enforced at the queryset level.

## Frontend Architecture

```
frontend/src/
├── modules/users/
│   ├── types.ts        # TypeScript interfaces
│   ├── api.ts          # API client functions
│   └── pages/          # 8 page components
├── shared/
│   ├── api/client.ts   # Axios + token interceptors
│   ├── auth/           # AuthProvider, ProtectedRoute
│   └── layout/         # Layout with sidebar + header
└── App.tsx             # Router + auth wrapping
```

## Key Design Decisions

1. **Stub User model** — `AUTH_USER_MODEL` points to a minimal `User` for FK relations; actual auth is handled by AUTHinator
2. **IntegerField PK** — `UserProfile.user_id` is an IntegerField PK matching AUTHinator's User.id (not a FK)
3. **JSONField for tags** — SQLite-compatible; no ArrayField dependency
4. **Numeric role levels** — Simple integer comparison for permissions; custom roles supported
5. **Company scoping at queryset level** — `CompanyScopedMixin` filters all queries by user's company

# USERinator

**User & Company Management** microservice for the Inator Platform.

USERinator is the authoritative source for user profiles, companies/organizations, role definitions, user preferences, and invitation workflows. It integrates with AUTHinator for authentication while owning all user profile and role data.

## Tech Stack

- **Backend:** Python 3.12+, Django 5.x, Django REST Framework
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS 4
- **Database:** SQLite (dev), PostgreSQL (production)
- **Testing:** Django TestCase (backend), Vitest + React Testing Library (frontend)
- **Build:** [Task](https://taskfile.dev) (go-task)

## Quick Start

### Platform Mode (Recommended)

If you're using the [Inator Platform](https://github.com/losomode/inator):

```bash
# From the platform root (inator/)
task setup           # Sets up all inators including USERinator
task start:all       # Starts all services + unified frontend + gateway

# Access at http://localhost:8080
```

### Standalone Mode

```bash
# Install backend dependencies
task backend:install

# Run database migrations
task backend:migrate

# Create default roles (ADMIN=100, MANAGER=30, MEMBER=10)
task backend:manage -- create_default_roles

# (Optional) Load demo data — 3 companies, 10 users, sample invitations
task backend:manage -- setup_demo_data

# Start backend dev server on port 8004
task backend:dev

# Install and start frontend (separate terminal)
task frontend:install
task frontend:dev
```

### Demo Database

The Inator Platform provides a complete demo database with realistic company and user data. See the [Demo Database Guide](https://github.com/losomode/inator/blob/main/docs/DEMO_DATABASE.md) for full details.

```bash
# From the platform root (inator/)
task setup:demodb        # Build demo databases
task demodb:activate     # Activate demo data
task restart:all         # Restart all services
```

**Demo data includes:**
- 4 companies: Acme Corporation, Globex Industries, Initech LLC, Wayne Enterprises
- 12 user profiles with different roles (2 admins, 4 managers, 6 members)
- Complete role hierarchy (ADMIN=100, MANAGER=30, MEMBER=10)
- Company associations demonstrating RBAC filtering

## Available Tasks

```bash
task --list              # List all tasks
task check               # Pre-commit checks (fmt + lint + test:coverage)
task test                # Run all tests (backend + frontend)
task backend:test:coverage   # Backend tests with ≥85% coverage enforcement
task frontend:test:coverage  # Frontend tests with ≥85% coverage enforcement
task build               # Build frontend for production
```

## Project Structure

```
Userinator/
├── backend/
│   ├── config/          # Django settings, URLs, WSGI/ASGI
│   ├── core/            # Auth, permissions, management commands
│   ├── users/           # User profiles, preferences, health check
│   ├── companies/       # Company/organization management
│   ├── roles/           # Role definitions (numeric level system)
│   └── invitations/     # Invitation & approval workflows
├── frontend/            # React SPA (served at /users/ via Caddy)
│   ├── src/
│   │   ├── App.tsx      # BrowserRouter (basename=/users) + routes
│   │   ├── main.tsx     # Entry point
│   │   ├── pages/       # Profile, UserList, Companies, Invitations, Preferences
│   │   ├── api.ts       # User-specific API calls
│   │   └── types.ts     # User-specific types
│   ├── vite.config.ts   # base=/users/, @inator/shared alias, Tailwind v4
│   └── package.json
├── docs/                # Integration & workflow docs
└── Taskfile.yml         # Build automation
```

## API Overview

All endpoints require Bearer token authentication via AUTHinator (except health check).

| Prefix | Resource |
|---|---|
| `GET /api/users/health/` | Health check (no auth) |
| `/api/users/` | User profiles (company-scoped) |
| `/api/users/me/` | Own profile shortcut |
| `/api/users/preferences/me/` | Own preferences |
| `/api/users/batch/` | Batch profile lookup |
| `/api/companies/` | Companies (admin: list/create) |
| `/api/companies/my/` | Own company shortcut |
| `/api/roles/` | Role definitions |
| `/api/invitations/` | Invitation workflows |

## Role System

Roles use numeric levels for permission comparison:

- **ADMIN** (100) — Platform administrator, full access across all companies
- **MANAGER** (30) — Company manager, can manage team and edit company data
- **MEMBER** (10) — Standard company member, read-only access to company data

Custom roles can be created by platform admins with any level 1-99.

### RBAC (Role-Based Access Control)

USERinator enforces company-scoped data access:

- **Platform admins** (no company affiliation):
  - View and manage all users across all companies
  - Create and manage companies
  - Full access to all profiles and preferences

- **Company users** (managers and members):
  - View only users within their own company
  - Cannot see other companies' data
  - Company field is immutable after creation (prevents company-hopping)

- **Permission levels**:
  - ADMIN (100): Can edit any user profile, manage companies
  - MANAGER (30): Can edit profiles within their company
  - MEMBER (10): Can only edit their own profile

See the [Demo Database Guide](https://github.com/losomode/inator/blob/main/docs/DEMO_DATABASE.md) for examples of RBAC in action.

## Management Commands

```bash
# Roles & demo data
task backend:manage -- create_default_roles
task backend:manage -- setup_demo_data

# Migration from AUTHinator
task backend:manage -- migrate_from_authinator --dry-run
task backend:manage -- migrate_from_authinator
task backend:manage -- verify_migration

# Service registry
task backend:manage -- register_service

# Invitation cleanup
task backend:manage -- expire_invitations
```

## Testing

```bash
# Backend: 186 tests, 96% coverage
task backend:test:coverage

# Frontend: 65 tests, 93% coverage
task frontend:test:coverage

# Full pre-commit check
task check
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all configuration options.

Key variables:
- `SECRET_KEY` — Django secret key
- `AUTHINATOR_API_URL` — AUTHinator service URL (default: `http://localhost:8001/api/auth/`)
- `DEPLOY_DOMAIN` — External domain for production deployment
- `SERVICE_REGISTRATION_KEY` — Key for service registry

## Port Configuration

| Service | Port | Gateway Path |
|---|---|---|
| USERinator Backend | 8004 | `/api/users/`, `/api/companies/`, `/api/roles/`, `/api/invitations/` |
| USERinator Frontend (Vite) | 3004 | `/users/` |
| Caddy Gateway | 8080 | All traffic |

## Related Services

- **AUTHinator** (:8001) — Authentication, JWT tokens
- **RMAinator** (:8002) — RMA management
- **FULFILinator** (:8003) — Fulfillment management

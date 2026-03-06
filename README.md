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
├── frontend/
│   └── src/
│       ├── modules/users/   # Pages, API, types
│       └── shared/          # Auth, layout, API client
├── docs/                # Integration & workflow docs
├── Taskfile.yml         # Build automation
└── SPECIFICATION.md     # Full project specification
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

- **ADMIN** (100) — Platform administrator, full access
- **MANAGER** (30) — Company manager, team management
- **MEMBER** (10) — Standard company member

Custom roles can be created by platform admins with any level 1-99.

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

| Service | Port |
|---|---|
| USERinator Backend | 8004 |
| USERinator Frontend (Vite) | 5173 |
| Unified Gateway (Caddy) | 8080 |

## Related Services

- **AUTHinator** (:8001) — Authentication, JWT tokens
- **RMAinator** (:8002) — RMA management
- **FULFILinator** (:8003) — Fulfillment management

# USERinator Phase 1.1.1: Initialize Repository Structure

## Problem
Initialize the USERinator repository with the correct Django project structure per INATOR.md section 2.1.

## Current State
- Empty project with only `AGENTS.md`, `deft/`, and `SPECIFICATION.md`
- No backend/, no .venv, no Django project

## Proposed Changes

### 1. Directory structure per INATOR.md 2.1
```
Userinator/
├── backend/
│   ├── config/           # Django project
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── core/             # Auth, permissions, client
│   ├── users/            # UserProfile app + stub User model
│   ├── companies/        # Company app
│   ├── roles/            # Role app
│   ├── invitations/      # Invitation app
│   ├── requirements.txt
│   └── manage.py
├── .venv/                # At ROOT, not backend/
├── .gitignore
└── Taskfile.yml
```

### 2. Key decisions
- `AUTH_USER_MODEL = 'users.User'` — stub User(AbstractUser) for FK relations (like RMAinator)
- UserProfile with user_id PK (IntegerField) will be separate model (Phase 1.2.3)
- REST_FRAMEWORK with `core.authentication.AuthinatorJWTAuthentication`
- Port 8004, CORS for :8080 gateway
- All 5 apps: core, users, companies, roles, invitations

### 3. Validation
- `python manage.py check` — passed (0 issues)
- `python manage.py makemigrations` — users migration created
- `python manage.py migrate` — all migrations applied
- `task --list` — all 32 tasks available

## Status: COMPLETED

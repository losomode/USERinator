# USERinator Deployment Guide

## Prerequisites

- Python 3.12+
- Node.js 20+
- [Task](https://taskfile.dev) (go-task)
- PostgreSQL (production)

## Environment Setup

### Backend (`backend/.env`)

```bash
# Security
SECRET_KEY=<generate-strong-key>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# External domain (enables HTTPS cookies automatically)
DEPLOY_DOMAIN=www.example.com
DEPLOY_SCHEME=https

# Database (production)
DATABASE_URL=postgresql://user:pass@host:5432/userinator

# AUTHinator integration
AUTHINATOR_API_URL=http://localhost:8001/api/auth/
AUTHINATOR_VERIFY_SSL=True

# Service registry
SERVICE_REGISTRY_URL=http://localhost:8001/api/services/register/
SERVICE_REGISTRATION_KEY=<secure-key>

# Email (production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=<app-password>
```

### Frontend (`frontend/.env`)

```bash
VITE_DEPLOY_DOMAIN=www.example.com
```

## Deployment Steps

1. **Install dependencies**
   ```bash
   task install
   ```

2. **Configure environment variables** (see above)

3. **Run database migrations**
   ```bash
   task backend:migrate
   ```

4. **Create default roles**
   ```bash
   task backend:manage -- create_default_roles
   ```

5. **Build frontend**
   ```bash
   task build
   ```

6. **Register with AUTHinator**
   ```bash
   task backend:manage -- register_service
   ```

7. **Start backend**
   ```bash
   task backend:dev
   ```

8. **Verify health check**
   ```bash
   curl http://localhost:8004/api/users/health/
   ```

## Production Checklist

- Set `DEBUG=False`
- Use a strong `SECRET_KEY`
- Configure `DEPLOY_DOMAIN` and `DEPLOY_SCHEME=https`
- Secure cookies are auto-enabled when `DEPLOY_DOMAIN` + `https` are set
- Configure PostgreSQL database
- Configure production email backend
- Run `create_default_roles`
- Register service with AUTHinator
- Update Caddyfile to route `/api/users/` → `localhost:8004`
- Verify health check via unified gateway

## Rollback

1. Stop USERinator backend
2. Revert database: `task backend:manage -- migrate <app> <previous_migration>`
3. Restart previous version

## Caddy Configuration

Add to the platform Caddyfile:

```
handle /api/users/* {
    reverse_proxy localhost:8004
}
```

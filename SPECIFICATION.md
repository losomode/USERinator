# USERinator Specification

## Overview

**USERinator** is the fourth microservice in the Inator Platform, responsible for managing user profiles, companies/organizations, and role definitions. It extracts user management functionality from AUTHinator, becoming the authoritative source for user profile data and role assignments while AUTHinator retains authentication responsibilities.

**Key Responsibilities:**
- User profile management (display name, avatar, bio, job title, etc.)
- Company/organization management with extended metadata
- Role definitions and assignments (ADMIN, MANAGER, MEMBER with numeric levels)
- User preferences (timezone, language, notifications)
- User invitation and approval workflows
- Company-scoped data access control

**Service Boundaries:**
- AUTHinator: Authentication, credentials, JWT tokens, MFA, SSO
- USERinator: User profiles, companies, roles, preferences, invitations
- Other Inators: Call USERinator API for user/company context

## Requirements

### Functional Requirements

#### User Profiles
- MUST store extended user profile data: display_name, avatar, phone, timezone, bio, job_title, department, location
- MUST associate each user with exactly one company
- MUST support company-scoped visibility (users only see profiles within their company)
- MUST allow users to update their own profile
- MUST allow company admins to view/edit all profiles in their company
- MUST allow platform admins (role_level=100) to view/edit all profiles
- MUST sync user_id, username, email with AUTHinator (stub User model pattern)

#### Companies/Organizations
- MUST support flat organizational structure (no teams/hierarchies in Phase 1)
- MUST store: name, address, phone, website, industry, company_size, logo, billing_contact
- MUST support extended metadata: custom_fields (JSON), tags (array), notes (admin-only), account_status
- MUST only allow platform admins to create companies
- MUST track company creation date and created_by admin
- MUST prevent company deletion if users exist (soft delete/archive pattern)

#### Role System
- MUST define roles with numeric levels: ADMIN=100, MANAGER=30, MEMBER=10
- MUST allow platform admins to create custom roles with configurable levels (e.g., SUPERVISOR=50)
- MUST store both role_name (string) and role_level (integer) for each user
- MUST be the authoritative source for all role data
- MUST provide API for AUTHinator to query user roles during login
- MUST support role comparison operations (user.role_level >= required_level)
- MUST include role information in JWT tokens (fetched by AUTHinator during login)
- SHOULD support role change events that trigger JWT token invalidation

#### User Preferences
- MUST support platform-wide preferences: timezone, language (en/es/etc.), notification_email, notification_in_app
- MUST default timezone to UTC if not set
- MUST default language to 'en' if not set
- MUST allow users to update their own preferences
- SHOULD provide preference inheritance (company defaults → user overrides)

#### User Invitations
- MUST implement approval workflow: user requests to join company → admin reviews → approve/reject
- MUST track invitation status: pending, approved, rejected, expired
- MUST send email notifications for invitation status changes
- MUST allow company admins to view pending invitations for their company
- MUST allow company admins to approve/reject invitations
- MUST create user profile in USERinator upon invitation approval
- MUST coordinate with AUTHinator for account creation after approval

#### API Access
- MUST provide RESTful API following INATOR.md patterns: `/api/users/`
- MUST implement caching headers (Cache-Control, ETag) for profile/company data
- MUST recommend 5-minute cache TTL for user profiles, 15-minute for company data
- MUST provide batch endpoints for efficient multi-user queries
- MUST follow INATOR.md authentication patterns (AuthinatorJWTAuthentication)

### Non-Functional Requirements

#### Performance
- MUST respond to profile queries in <100ms (p95)
- MUST support 1000+ concurrent users per company
- SHOULD implement database indexes on: user_id, company_id, role_level
- SHOULD use select_related/prefetch_related for nested queries

#### Security
- MUST enforce company-scoped data access (users cannot see other companies)
- MUST validate all role changes require appropriate permissions
- MUST prevent privilege escalation (cannot assign role_level higher than own)
- MUST audit all role changes with timestamp and changed_by
- MUST validate all input at API boundaries
- MUST prevent SQL injection, XSS, CSRF attacks

#### Quality
- MUST achieve ≥85% test coverage (per INATOR.md)
- MUST pass all linting (ruff) and formatting (black) checks
- MUST implement unit tests for models, serializers, business logic
- MUST implement integration tests for API endpoints
- MUST implement E2E tests for critical flows (profile update, role assignment, invitation approval)
- MUST follow Deft TDD approach: write tests before implementation

#### Compliance
- MUST follow INATOR.md standards completely
- MUST use port 8004 for backend service
- MUST implement Taskfile.yml with standard tasks
- MUST use python-decouple for environment variables
- MUST support DEPLOY_DOMAIN for external deployment
- MUST register with AUTHinator service registry

## Architecture

### System Context

```
┌─────────────┐
│ AUTHinator  │──────> Authenticates user
│   :8001     │        Calls USERinator for role
└─────────────┘        Includes role in JWT
       │
       ▼
┌─────────────┐
│ USERinator  │◄────── Source of truth for:
│   :8004     │        - User profiles
└─────────────┘        - Companies
       │               - Roles (definitions + assignments)
       │               - Preferences
       ▼
┌─────────────┐
│ RMAinator   │◄────── Reads user/company context
│ FULFILinator│        Checks role_level for permissions
│   :8002/3   │        Caches profile data (5min TTL)
└─────────────┘
```

### Data Model

#### Core Models

```python
# User Profile (Primary Model)
class UserProfile(models.Model):
    # Synced from AUTHinator (stub pattern)
    user_id = IntegerField(primary_key=True)  # Matches AUTHinator User.id
    username = CharField(max_length=150, unique=True)
    email = EmailField()
    
    # Company relationship
    company = ForeignKey(Company, on_delete=PROTECT)
    
    # Profile data
    display_name = CharField(max_length=255)
    avatar_url = URLField(blank=True)
    phone = CharField(max_length=50, blank=True)
    bio = TextField(blank=True)
    job_title = CharField(max_length=100, blank=True)
    department = CharField(max_length=100, blank=True)
    location = CharField(max_length=255, blank=True)
    
    # Role (numeric level system)
    role_name = CharField(max_length=50)  # ADMIN, MANAGER, MEMBER, custom
    role_level = IntegerField()  # 100, 30, 10, custom
    
    # Preferences
    timezone = CharField(max_length=50, default='UTC')
    language = CharField(max_length=10, default='en')
    notification_email = BooleanField(default=True)
    notification_in_app = BooleanField(default=True)
    
    # Metadata
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    last_synced_at = DateTimeField(auto_now=True)  # Last sync from AUTHinator

# Company
class Company(models.Model):
    name = CharField(max_length=255, unique=True)
    
    # Standard business info
    address = TextField(blank=True)
    phone = CharField(max_length=50, blank=True)
    website = URLField(blank=True)
    industry = CharField(max_length=100, blank=True)
    company_size = CharField(max_length=50, blank=True)  # "1-10", "11-50", etc.
    logo_url = URLField(blank=True)
    billing_contact_email = EmailField(blank=True)
    
    # Extended metadata
    custom_fields = JSONField(default=dict, blank=True)  # Flexible JSON storage
    tags = ArrayField(CharField(max_length=50), default=list, blank=True)
    notes = TextField(blank=True)  # Admin-only notes
    account_status = CharField(max_length=20, default='active')  # active, suspended, archived
    
    # Audit
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True)
    
    class Meta:
        indexes = [Index(fields=['account_status'])]

# Role Definition
class Role(models.Model):
    role_name = CharField(max_length=50, unique=True)  # ADMIN, MANAGER, MEMBER, etc.
    role_level = IntegerField(unique=True)  # 100, 50, 30, 10, etc.
    description = TextField(blank=True)
    is_system_role = BooleanField(default=False)  # True for ADMIN/MANAGER/MEMBER
    
    # Audit
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True)
    
    class Meta:
        ordering = ['-role_level']

# User Invitation
class UserInvitation(models.Model):
    class Status(TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
    
    email = EmailField()
    company = ForeignKey(Company, on_delete=CASCADE)
    requested_role = ForeignKey(Role, on_delete=PROTECT)
    status = CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Request info
    requested_at = DateTimeField(auto_now_add=True)
    requested_by_user_id = IntegerField(null=True)  # If existing user requests
    message = TextField(blank=True)
    
    # Review info
    reviewed_at = DateTimeField(null=True)
    reviewed_by = ForeignKey(settings.AUTH_USER_MODEL, on_delete=SET_NULL, null=True, related_name='reviewed_invitations')
    review_notes = TextField(blank=True)
    
    # Expiration
    expires_at = DateTimeField()  # Default: requested_at + 7 days
    
    class Meta:
        indexes = [
            Index(fields=['email', 'company', 'status']),
            Index(fields=['status', 'expires_at'])
        ]
```

### API Endpoints

Following INATOR.md REST conventions:

```
# User Profiles
GET    /api/users/                    # List users (company-scoped)
POST   /api/users/                    # Create user profile (admin only)
GET    /api/users/{id}/               # Get user profile
PATCH  /api/users/{id}/               # Update user profile (self or admin)
DELETE /api/users/{id}/               # Deactivate user (admin only)
GET    /api/users/me/                 # Get own profile (shortcut)
PATCH  /api/users/me/                 # Update own profile
GET    /api/users/{id}/permissions/   # Get user permissions (for other services)

# Companies
GET    /api/companies/                # List companies (admin only)
POST   /api/companies/                # Create company (platform admin only)
GET    /api/companies/{id}/           # Get company details
PATCH  /api/companies/{id}/           # Update company (company admin)
GET    /api/companies/{id}/users/     # List company users
GET    /api/companies/my/             # Get own company (shortcut)

# Roles
GET    /api/roles/                    # List all role definitions
POST   /api/roles/                    # Create custom role (platform admin)
GET    /api/roles/{id}/               # Get role definition
PATCH  /api/roles/{id}/               # Update role (platform admin)
DELETE /api/roles/{id}/               # Delete custom role (platform admin)

# Invitations
GET    /api/invitations/              # List invitations (company-scoped for admins)
POST   /api/invitations/              # Request to join company
GET    /api/invitations/{id}/         # Get invitation details
POST   /api/invitations/{id}/approve/ # Approve invitation (company admin)
POST   /api/invitations/{id}/reject/  # Reject invitation (company admin)

# Preferences
GET    /api/preferences/me/           # Get own preferences
PATCH  /api/preferences/me/           # Update own preferences

# Health & Service Registry
GET    /api/users/health/             # Health check
POST   /api/users/register-service/   # Service registry (internal)
```

### Authentication Pattern

Following INATOR.md non-Authinator service pattern:

```python
# core/authentication.py
class AuthinatorJWTAuthentication(authentication.BaseAuthentication):
    """
    Validates JWT with AUTHinator, creates/syncs local UserProfile stub.
    Attaches role_level and company_id to request.user for permissions.
    """
    def authenticate(self, request):
        # Extract Bearer token
        # Validate with AUTHinator /api/auth/verify/
        # Get or sync UserProfile by user_id
        # Attach role_level, company_id attributes
        return (user_profile, token)

# core/permissions.py
class IsCompanyAdmin(BasePermission):
    """User must be admin of their company (role_level >= 30)"""
    def has_permission(self, request, view):
        return request.user.role_level >= 30

class IsPlatformAdmin(BasePermission):
    """User must be platform admin (role_level >= 100)"""
    def has_permission(self, request, view):
        return request.user.role_level >= 100

class IsOwnerOrCompanyAdmin(BasePermission):
    """User must own resource or be company admin"""
    def has_object_permission(self, request, view, obj):
        if request.user.role_level >= 30:
            return obj.company_id == request.user.company_id
        return obj.user_id == request.user.user_id
```

## Implementation Plan

### Phase 1: Foundation (depends on: none)

Build core USERinator service infrastructure following INATOR.md standards.

#### Subphase 1.1: Project Setup

**Task 1.1.1: Initialize repository structure**
- Dependencies: None
- Actions:
  - Create Userinator/ directory with backend/, frontend/ structure
  - Initialize Django project: `backend/config/`
  - Create core Django apps: core/, users/, companies/, roles/, invitations/
  - Create .venv at repository root (NOT in backend/)
  - Create requirements.txt with minimum dependencies
  - Create .gitignore following INATOR.md
- Acceptance Criteria:
  - Directory structure matches INATOR.md section 2.1
  - `python manage.py check` passes
  - All apps installed in INSTALLED_APPS
- Testing: Run django checks, verify directory layout

**Task 1.1.2: Configure Django settings**
- Dependencies: 1.1.1
- Actions:
  - Implement settings.py following INATOR.md section 2.2
  - Add python-decouple for environment variables
  - Configure DEPLOY_DOMAIN support (section 2.2.3)
  - Configure CORS for unified gateway (section 2.2.4)
  - Configure CSRF trusted origins (section 2.2.5)
  - Set REST_FRAMEWORK with AuthinatorJWTAuthentication
  - Set port 8004 for backend
- Acceptance Criteria:
  - All required settings match INATOR.md
  - Environment variables load from .env
  - CORS allows http://localhost:8080
- Testing: Django check, test with various DEPLOY_DOMAIN values

**Task 1.1.3: Create .env.example templates**
- Dependencies: 1.1.2
- Actions:
  - Create backend/.env.example following INATOR.md section 5.1
  - Add AUTHINATOR_API_URL, SERVICE_REGISTRY_URL
  - Create frontend/.env.example with VITE_DEPLOY_DOMAIN
- Acceptance Criteria:
  - .env.example matches non-Authinator template
  - All required env vars documented
- Testing: Manual verification of template completeness

**Task 1.1.4: Implement Taskfile.yml**
- Dependencies: 1.1.1
- Actions:
  - Create Taskfile.yml at repository root
  - Implement all required backend tasks (section 4.2)
  - Implement all required frontend tasks (section 4.2)
  - Set COVERAGE_THRESHOLD: 85
  - Set PROJECT_NAME: Userinator
  - Configure port 8004 for backend:dev
- Acceptance Criteria:
  - All MUST tasks from INATOR.md section 4.2 present
  - `task --list` shows all tasks
  - `task backend:install` creates .venv at root
- Testing: Run task backend:install, task backend:test

#### Subphase 1.2: Authentication & Core Infrastructure (depends on: 1.1)

**Task 1.2.1: Implement AuthinatorJWTAuthentication**
- Dependencies: 1.1.4
- Actions:
  - Create core/authinator_client.py for API calls
  - Implement AuthinatorJWTAuthentication class
  - Implement token validation with AUTHinator
  - Create/sync local UserProfile on authentication
  - Attach role_level, company_id to request.user
- Acceptance Criteria:
  - Authentication validates tokens with AUTHinator
  - UserProfile created/synced from token data
  - request.user has role_level, company_id attributes
- Testing: Unit tests for authentication flow, integration test with mock AUTHinator

**Task 1.2.2: Implement permission classes**
- Dependencies: 1.2.1
- Actions:
  - Create core/permissions.py
  - Implement IsCompanyAdmin (role_level >= 30)
  - Implement IsPlatformAdmin (role_level >= 100)
  - Implement IsOwnerOrCompanyAdmin
  - Implement CompanyScopedPermission
- Acceptance Criteria:
  - All permission classes follow INATOR.md patterns
  - Permissions check role_level correctly
  - Company scoping prevents cross-company access
- Testing: Unit tests for each permission class with various role levels

**Task 1.2.3: Create database models**
- Dependencies: 1.2.1
- Actions:
  - Implement UserProfile model with all fields
  - Implement Company model with extended metadata
  - Implement Role model with numeric levels
  - Implement UserInvitation model with status workflow
  - Create database migrations
  - Add indexes following INATOR.md section 2.7.2
- Acceptance Criteria:
  - All models match specification data model
  - Migrations created and applied
  - Database indexes on key fields
- Testing: Model tests for properties, constraints, relationships

**Task 1.2.4: Create initial data fixtures**
- Dependencies: 1.2.3
- Actions:
  - Create management command: create_default_roles
  - Seed roles: ADMIN=100, MANAGER=30, MEMBER=10
  - Mark system roles (is_system_role=True)
  - Create demo company for development
- Acceptance Criteria:
  - Three system roles created
  - Demo company exists for testing
  - Command is idempotent
- Testing: Run command multiple times, verify data consistency

#### Subphase 1.3: Testing Infrastructure (depends on: 1.2)

**Task 1.3.1: Configure pytest and coverage**
- Dependencies: 1.2.4
- Actions:
  - Add pytest-django, coverage to requirements.txt
  - Create pytest.ini configuration
  - Configure coverage settings (≥85% threshold)
  - Create conftest.py with common fixtures
  - Implement test database setup
- Acceptance Criteria:
  - `task backend:test` runs pytest
  - `task backend:test:coverage` enforces 85% threshold
  - Fixtures available: test_user, test_company, test_admin
- Testing: Run pytest with empty test suite, verify configuration

**Task 1.3.2: Write core model tests**
- Dependencies: 1.3.1
- Actions:
  - Test UserProfile model methods and properties
  - Test Company model validation and constraints
  - Test Role model uniqueness and ordering
  - Test UserInvitation status transitions
  - Test all model relationships (ForeignKey, CASCADE)
- Acceptance Criteria:
  - All model tests pass
  - Coverage for models/ directory ≥85%
  - Tests follow INATOR.md testing patterns
- Testing: Run `task backend:test:coverage`, verify model coverage

**Task 1.3.3: Write authentication tests**
- Dependencies: 1.3.1, 1.2.1
- Actions:
  - Test AuthinatorJWTAuthentication with valid token
  - Test authentication with invalid/expired token
  - Test UserProfile sync on authentication
  - Test role_level attribute attachment
  - Mock AUTHinator API responses
- Acceptance Criteria:
  - All authentication paths tested
  - Integration tests with mocked AUTHinator
  - Coverage for core/authentication.py ≥85%
- Testing: Run authentication tests with various token scenarios

### Phase 2: User Profile Management (depends on: Phase 1)

Implement user profile CRUD operations with company scoping.

#### Subphase 2.1: Profile API (depends on: 1.3)

**Task 2.1.1: Implement profile serializers**
- Dependencies: 1.3.3
- Actions:
  - Create UserProfileListSerializer (summary fields)
  - Create UserProfileDetailSerializer (all fields)
  - Create UserProfileUpdateSerializer (editable fields)
  - Implement to_representation for company scoping
  - Filter sensitive fields based on role_level
- Acceptance Criteria:
  - All serializers follow INATOR.md section 2.5.2
  - Read-only fields properly marked
  - Company-scoped data filtering
- Testing: Serializer tests with various user roles

**Task 2.1.2: Implement profile views**
- Dependencies: 2.1.1
- Actions:
  - Create UserProfileListCreateView (GET, POST)
  - Create UserProfileDetailView (GET, PATCH, DELETE)
  - Create UserProfileMeView (GET, PATCH)
  - Implement get_queryset with company scoping
  - Apply permission classes (IsAuthenticated, IsCompanyAdmin)
- Acceptance Criteria:
  - All views follow INATOR.md section 2.5.1
  - Company scoping prevents cross-company access
  - Permissions enforce role_level requirements
- Testing: API endpoint tests for each view, permission tests

**Task 2.1.3: Configure profile URLs**
- Dependencies: 2.1.2
- Actions:
  - Create users/urls.py
  - Configure RESTful URL patterns
  - Mount at /api/users/ in config/urls.py
  - Follow INATOR.md URL conventions
- Acceptance Criteria:
  - URLs match API specification
  - /api/users/me/ shortcut works
  - URL reversing works correctly
- Testing: URL resolution tests, reverse URL tests

**Task 2.1.4: Write profile API tests**
- Dependencies: 2.1.3
- Actions:
  - Test profile list endpoint (company-scoped)
  - Test profile detail endpoint (own + admin)
  - Test profile update (self-update restrictions)
  - Test profile permissions (cross-company denial)
  - Test /api/users/me/ convenience endpoint
- Acceptance Criteria:
  - All profile endpoints tested
  - Integration tests with authentication
  - Coverage for users/ app ≥85%
- Testing: Run full API test suite with various roles

#### Subphase 2.2: Profile Search & Batch Operations (depends on: 2.1)

**Task 2.2.1: Implement profile search**
- Dependencies: 2.1.4
- Actions:
  - Add search filters (display_name, email, job_title)
  - Implement Q() queries for multi-field search
  - Add role_level filtering
  - Maintain company scoping on search
- Acceptance Criteria:
  - Search works across multiple fields
  - Company scoping preserved
  - Performance acceptable (<100ms p95)
- Testing: Search tests with various query combinations

**Task 2.2.2: Implement batch profile endpoint**
- Dependencies: 2.1.4
- Actions:
  - Create /api/users/batch/ endpoint
  - Accept list of user_ids in request body
  - Return profiles for requested users (company-scoped)
  - Optimize with select_related/prefetch_related
- Acceptance Criteria:
  - Batch endpoint accepts 1-100 user_ids
  - Returns only accessible profiles
  - Single database query for all profiles
- Testing: Batch query tests, performance tests

### Phase 3: Company Management (depends on: Phase 1)

Implement company CRUD and metadata management.

#### Subphase 3.1: Company API (depends on: 1.3)

**Task 3.1.1: Implement company serializers**
- Dependencies: 1.3.3
- Actions:
  - Create CompanyListSerializer (summary)
  - Create CompanyDetailSerializer (full data)
  - Create CompanyCreateSerializer (admin-only)
  - Create CompanyUpdateSerializer (editable fields)
  - Handle custom_fields JSON validation
- Acceptance Criteria:
  - All serializers follow INATOR.md patterns
  - custom_fields validated as JSON
  - Extended metadata fields included
- Testing: Serializer tests with valid/invalid data

**Task 3.1.2: Implement company views**
- Dependencies: 3.1.1
- Actions:
  - Create CompanyListCreateView (platform admin only)
  - Create CompanyDetailView (GET, PATCH)
  - Create CompanyUsersView (list users in company)
  - Create CompanyMyView (get own company)
  - Apply IsPlatformAdmin for creation
- Acceptance Criteria:
  - Only platform admins can create companies
  - Company admins can update their company
  - Company users list is company-scoped
- Testing: Company API tests with admin/non-admin users

**Task 3.1.3: Configure company URLs**
- Dependencies: 3.1.2
- Actions:
  - Create companies/urls.py
  - Configure RESTful patterns
  - Add /api/companies/my/ shortcut
  - Mount at /api/companies/
- Acceptance Criteria:
  - URLs match API specification
  - Convenience endpoints work
- Testing: URL resolution tests

**Task 3.1.4: Write company API tests**
- Dependencies: 3.1.3
- Actions:
  - Test company creation (admin-only)
  - Test company update (permissions)
  - Test company user list (scoping)
  - Test extended metadata (custom_fields, tags)
  - Test /api/companies/my/ endpoint
- Acceptance Criteria:
  - All company endpoints tested
  - Coverage for companies/ app ≥85%
- Testing: Run company test suite

### Phase 4: Role System (depends on: Phase 1)

Implement role definitions and numeric level system.

#### Subphase 4.1: Role Management API (depends on: 1.3)

**Task 4.1.1: Implement role serializers**
- Dependencies: 1.3.3
- Actions:
  - Create RoleSerializer (all fields)
  - Create RoleCreateSerializer (validation)
  - Validate role_name uniqueness
  - Validate role_level uniqueness and range (1-100)
  - Prevent modification of system roles
- Acceptance Criteria:
  - Role validation prevents conflicts
  - System roles cannot be edited/deleted
  - Custom roles validated correctly
- Testing: Role serializer tests with edge cases

**Task 4.1.2: Implement role views**
- Dependencies: 4.1.1
- Actions:
  - Create RoleListCreateView (platform admin)
  - Create RoleDetailView (GET, PATCH, DELETE)
  - Implement system role protection
  - Prevent role_level conflicts
- Acceptance Criteria:
  - Only platform admins manage roles
  - System roles protected from changes
  - Custom roles can be created/deleted
- Testing: Role API tests with system/custom roles

**Task 4.1.3: Implement role assignment**
- Dependencies: 4.1.2, 2.1.2
- Actions:
  - Add role assignment to UserProfile update
  - Validate role_level privileges (cannot assign higher than own)
  - Prevent privilege escalation
  - Track role changes in audit log
- Acceptance Criteria:
  - Role assignment follows privilege rules
  - Audit trail for role changes
  - Validation prevents escalation
- Testing: Role assignment tests with various scenarios

**Task 4.1.4: Write role system tests**
- Dependencies: 4.1.3
- Actions:
  - Test role CRUD operations
  - Test role assignment and validation
  - Test privilege escalation prevention
  - Test system role protection
  - Test role_level comparison logic
- Acceptance Criteria:
  - All role operations tested
  - Coverage for roles/ app ≥85%
- Testing: Run role test suite

#### Subphase 4.2: AUTHinator Integration (depends on: 4.1)

**Task 4.2.1: Create role query endpoint for AUTHinator**
- Dependencies: 4.1.4
- Actions:
  - Create internal API endpoint: /api/users/{id}/role/
  - Return role_name and role_level for JWT token
  - Add service authentication (SERVICE_REGISTRATION_KEY)
  - Optimize for low latency (<50ms)
- Acceptance Criteria:
  - Endpoint returns role data in <50ms
  - Authenticated by service key
  - Used by AUTHinator during login
- Testing: Integration test with mocked AUTHinator

**Task 4.2.2: Document AUTHinator integration changes**
- Dependencies: 4.2.1
- Actions:
  - Create docs/AUTHINATOR_INTEGRATION.md
  - Document role query API
  - Document JWT token changes (add role_level claim)
  - Document token invalidation on role change
  - Provide migration checklist
- Acceptance Criteria:
  - Integration documentation complete
  - AUTHinator team can implement changes
  - Migration path clear
- Testing: Manual review of documentation

### Phase 5: User Invitations (depends on: Phase 2, Phase 3)

Implement invitation and approval workflow.

#### Subphase 5.1: Invitation API (depends on: 2.1, 3.1)

**Task 5.1.1: Implement invitation serializers**
- Dependencies: 2.1.4, 3.1.4
- Actions:
  - Create InvitationSerializer (all fields)
  - Create InvitationCreateSerializer (user-facing)
  - Create InvitationReviewSerializer (admin approval)
  - Validate email uniqueness within company
  - Set default expiration (7 days)
- Acceptance Criteria:
  - Invitation validation prevents duplicates
  - Expiration date auto-calculated
  - Status transitions validated
- Testing: Invitation serializer tests

**Task 5.1.2: Implement invitation views**
- Dependencies: 5.1.1
- Actions:
  - Create InvitationListCreateView
  - Create InvitationDetailView
  - Create InvitationApproveView (POST)
  - Create InvitationRejectView (POST)
  - Filter by status and company
- Acceptance Criteria:
  - Users can request to join companies
  - Company admins can review invitations
  - Status workflow enforced (pending→approved/rejected)
- Testing: Invitation API tests with workflow

**Task 5.1.3: Implement invitation notifications**
- Dependencies: 5.1.2
- Actions:
  - Send email on invitation request (to admins)
  - Send email on approval (to user)
  - Send email on rejection (to user)
  - Use Django email backend (console for dev)
  - Template emails with invitation details
- Acceptance Criteria:
  - Email notifications sent for status changes
  - Templates include relevant information
  - Console backend works in dev
- Testing: Email notification tests with mock backend

**Task 5.1.4: Implement invitation expiration**
- Dependencies: 5.1.2
- Actions:
  - Create management command: expire_invitations
  - Mark expired invitations (status=EXPIRED)
  - Add Taskfile task for cron scheduling
  - Run on application startup (check expired)
- Acceptance Criteria:
  - Expired invitations marked automatically
  - Command runs without errors
  - Can be scheduled via cron/systemd
- Testing: Expiration command tests with various dates

**Task 5.1.5: Write invitation tests**
- Dependencies: 5.1.4
- Actions:
  - Test invitation creation and validation
  - Test approval workflow (pending→approved)
  - Test rejection workflow (pending→rejected)
  - Test expiration logic
  - Test email notifications
  - Test permission checks (company admin only)
- Acceptance Criteria:
  - All invitation flows tested
  - Coverage for invitations/ app ≥85%
- Testing: Run invitation test suite

#### Subphase 5.2: Account Creation Integration (depends on: 5.1)

**Task 5.2.1: Coordinate with AUTHinator on approval**
- Dependencies: 5.1.5
- Actions:
  - Call AUTHinator API on invitation approval
  - Trigger account creation email from AUTHinator
  - Store user_id when AUTHinator creates account
  - Handle AUTHinator errors gracefully
- Acceptance Criteria:
  - Approval triggers AUTHinator account creation
  - UserProfile created with correct role
  - Error handling for AUTHinator failures
- Testing: Integration test with mocked AUTHinator

**Task 5.2.2: Document invitation workflow**
- Dependencies: 5.2.1
- Actions:
  - Create docs/INVITATION_WORKFLOW.md
  - Document user journey (request→review→account)
  - Document admin actions and permissions
  - Provide API examples
- Acceptance Criteria:
  - Workflow documentation complete
  - Includes sequence diagrams
  - API examples provided
- Testing: Manual review of documentation

### Phase 6: Preferences & Settings (depends on: Phase 2)

Implement user preference management.

#### Subphase 6.1: Preferences API (depends on: 2.1)

**Task 6.1.1: Implement preference serializers**
- Dependencies: 2.1.4
- Actions:
  - Create PreferencesSerializer (timezone, language, notifications)
  - Validate timezone against pytz.all_timezones
  - Validate language against supported languages
  - Provide defaults (UTC, en, all notifications on)
- Acceptance Criteria:
  - Preference validation works
  - Defaults applied correctly
  - Invalid timezones rejected
- Testing: Preference serializer tests

**Task 6.1.2: Implement preference views**
- Dependencies: 6.1.1
- Actions:
  - Create PreferencesMeView (GET, PATCH)
  - Users can only manage own preferences
  - Merge with UserProfile model (no separate table)
  - Return updated preferences immediately
- Acceptance Criteria:
  - /api/preferences/me/ endpoint works
  - Users can update own preferences only
  - Changes persist in UserProfile
- Testing: Preference API tests

**Task 6.1.3: Write preference tests**
- Dependencies: 6.1.2
- Actions:
  - Test preference retrieval
  - Test preference updates
  - Test timezone validation
  - Test language validation
  - Test permission checks
- Acceptance Criteria:
  - All preference operations tested
  - Validation tests for each field
- Testing: Run preference test suite

### Phase 7: Frontend Integration (depends on: Phase 6)

Build React frontend following INATOR.md patterns.

#### Subphase 7.1: Frontend Setup (depends on: none, parallel to backend)

**Task 7.1.1: Initialize frontend project**
- Dependencies: None
- Actions:
  - Create frontend/ directory structure
  - Initialize Vite + React + TypeScript
  - Install dependencies: axios, react-router-dom, tailwindcss
  - Configure vite.config.ts with allowedHosts
  - Create src/ structure: modules/, shared/
- Acceptance Criteria:
  - Directory structure matches INATOR.md section 3.2
  - `npm run dev` starts Vite on port 5173
  - TypeScript strict mode enabled
- Testing: Run dev server, verify build

**Task 7.1.2: Create API client**
- Dependencies: 7.1.1
- Actions:
  - Create src/shared/api/client.ts following INATOR.md section 3.3
  - Configure axios with baseURL: '/api'
  - Implement token interceptors
  - Implement 401 error handling
  - Export getToken, setToken, clearToken
- Acceptance Criteria:
  - API client uses relative paths
  - Token attached to all requests
  - 401 redirects to login
- Testing: API client unit tests

**Task 7.1.3: Create TypeScript types**
- Dependencies: 7.1.1
- Actions:
  - Create src/modules/users/types.ts
  - Define UserProfile, Company, Role, Invitation interfaces
  - Mirror Django model structure
  - Use ISO date strings for DateTimeFields
- Acceptance Criteria:
  - All backend models have TS interfaces
  - Types match API response structure
- Testing: Type checking with tsc

**Task 7.1.4: Implement API module**
- Dependencies: 7.1.2, 7.1.3
- Actions:
  - Create src/modules/users/api.ts following INATOR.md section 3.4
  - Implement userApi: list, get, update, getMe, updateMe
  - Implement companyApi: get, update, getMy
  - Implement invitationApi: list, create, approve, reject
  - Implement roleApi: list
- Acceptance Criteria:
  - All API functions return typed promises
  - Error handling implemented
  - Functions follow INATOR.md patterns
- Testing: API module unit tests with mocked axios

#### Subphase 7.2: User Profile Pages (depends on: 7.1, 2.1)

**Task 7.2.1: Create profile view page**
- Dependencies: 7.1.4, 2.1.4
- Actions:
  - Create src/modules/users/pages/ProfilePage.tsx
  - Display user profile with all fields
  - Show company information
  - Show role and role_level
  - Implement loading states
- Acceptance Criteria:
  - Profile displays all user data
  - Loading spinner during fetch
  - Error handling for API failures
- Testing: Component tests with React Testing Library

**Task 7.2.2: Create profile edit page**
- Dependencies: 7.2.1
- Actions:
  - Create src/modules/users/pages/ProfileEditPage.tsx
  - Form for editing profile fields
  - Validate required fields
  - Show success/error messages
  - Redirect after save
- Acceptance Criteria:
  - Form validates input
  - Updates saved to API
  - User feedback for success/error
- Testing: Form interaction tests

**Task 7.2.3: Create user list page**
- Dependencies: 7.1.4, 2.1.4
- Actions:
  - Create src/modules/users/pages/UserListPage.tsx
  - Display table of company users
  - Show display_name, job_title, role
  - Link to profile detail
  - Filter by role (admin only)
- Acceptance Criteria:
  - User list shows company-scoped data
  - Clickable rows to profile detail
  - Admin sees role filter
- Testing: List page component tests

#### Subphase 7.3: Company Management Pages (depends on: 7.1, 3.1)

**Task 7.3.1: Create company view page**
- Dependencies: 7.1.4, 3.1.4
- Actions:
  - Create src/modules/users/pages/CompanyPage.tsx
  - Display company information
  - Show extended metadata (tags, custom_fields)
  - Company admin can edit
  - Link to user list
- Acceptance Criteria:
  - Company data displayed
  - Edit button for admins
  - Custom fields rendered as JSON
- Testing: Company page component tests

**Task 7.3.2: Create company edit page**
- Dependencies: 7.3.1
- Actions:
  - Create src/modules/users/pages/CompanyEditPage.tsx
  - Form for editing company fields
  - Support tags (multi-input)
  - Support custom_fields (JSON editor or key-value pairs)
  - Admin-only access
- Acceptance Criteria:
  - Company fields editable
  - Tags can be added/removed
  - Custom fields manageable
- Testing: Company edit form tests

#### Subphase 7.4: Invitation Pages (depends on: 7.1, 5.1)

**Task 7.4.1: Create invitation request page**
- Dependencies: 7.1.4, 5.1.5
- Actions:
  - Create src/modules/users/pages/InvitationRequestPage.tsx
  - Form to request company invitation
  - Select company from list
  - Select desired role
  - Add optional message
- Acceptance Criteria:
  - Form submits invitation request
  - Success confirmation shown
  - Error handling for duplicates
- Testing: Invitation request form tests

**Task 7.4.2: Create invitation review page**
- Dependencies: 7.1.4, 5.1.5
- Actions:
  - Create src/modules/users/pages/InvitationReviewPage.tsx
  - List pending invitations (admin only)
  - Show requester email, role, message
  - Approve/reject buttons
  - Confirmation dialogs
- Acceptance Criteria:
  - Admins see pending invitations
  - Can approve/reject with confirmation
  - List updates after action
- Testing: Invitation review component tests

#### Subphase 7.5: E2E Tests (depends on: 7.2, 7.3, 7.4)

**Task 7.5.1: Set up E2E testing framework**
- Dependencies: 7.1.4
- Actions:
  - Add Playwright or Cypress to devDependencies
  - Configure E2E test environment
  - Create test fixtures (users, companies)
  - Create page object models
- Acceptance Criteria:
  - E2E framework configured
  - Can run tests against dev server
  - Fixtures available
- Testing: Run sample E2E test

**Task 7.5.2: Write critical flow E2E tests**
- Dependencies: 7.5.1, 7.2.2, 7.3.2, 7.4.2
- Actions:
  - Test profile update flow (login → edit → save → verify)
  - Test company edit flow (admin login → company → edit → save)
  - Test invitation flow (request → admin approve → check profile)
  - Test role change flow (admin → user → change role → verify)
- Acceptance Criteria:
  - All critical user flows tested E2E
  - Tests run in CI environment
  - Tests pass consistently
- Testing: Run E2E test suite

### Phase 8: Migration & Integration (depends on: Phase 7)

Migrate existing data and integrate with other services.

#### Subphase 8.1: Data Migration from AUTHinator (depends on: 7.5)

**Task 8.1.1: Create data migration script**
- Dependencies: 7.5.2
- Actions:
  - Create management command: migrate_from_authinator
  - Fetch all users from AUTHinator API
  - Create Company records (group users by domain or manually)
  - Create UserProfile records with default values
  - Map AUTHinator roles to USERinator roles
  - Dry-run mode for testing
- Acceptance Criteria:
  - Script migrates all users successfully
  - Roles mapped correctly (ADMIN→100, USER→10)
  - Dry-run shows plan without changes
- Testing: Migration tests with test data

**Task 8.1.2: Verify data integrity**
- Dependencies: 8.1.1
- Actions:
  - Compare user counts (AUTHinator vs USERinator)
  - Verify role mappings
  - Check for duplicate users
  - Validate company assignments
  - Generate migration report
- Acceptance Criteria:
  - All users migrated
  - No data loss
  - Report shows success metrics
- Testing: Data validation scripts

**Task 8.1.3: Update AUTHinator to query USERinator**
- Dependencies: 8.1.2
- Actions:
  - Modify AUTHinator login flow to call USERinator
  - Add role_level claim to JWT tokens
  - Keep username/email in AUTHinator (stub pattern)
  - Test token generation with new claims
- Acceptance Criteria:
  - AUTHinator calls /api/users/{id}/role/ on login
  - JWT tokens include role_level
  - Backward compatible with old tokens (grace period)
- Testing: Integration tests with AUTHinator

#### Subphase 8.2: Update Other Inators (depends on: 8.1)

**Task 8.2.1: Update RMAinator for USERinator**
- Dependencies: 8.1.3
- Actions:
  - Add USERinator API calls for user profiles
  - Implement caching (5min TTL) for profiles
  - Update permission checks to use role_level
  - Test with new JWT token format
- Acceptance Criteria:
  - RMAinator displays user profiles from USERinator
  - Permission checks use role_level
  - Caching reduces API calls
- Testing: RMAinator integration tests

**Task 8.2.2: Update FULFILinator for USERinator**
- Dependencies: 8.1.3
- Actions:
  - Add USERinator API calls for user profiles
  - Implement caching for profiles
  - Update permission checks to use role_level
  - Test with new JWT token format
- Acceptance Criteria:
  - FULFILinator displays user profiles from USERinator
  - Permission checks use role_level
  - Caching implemented
- Testing: FULFILinator integration tests

**Task 8.2.3: Document migration process**
- Dependencies: 8.2.2
- Actions:
  - Create docs/MIGRATION_GUIDE.md
  - Document step-by-step migration process
  - Document rollback procedures
  - Document testing checklist
  - Provide troubleshooting guide
- Acceptance Criteria:
  - Migration guide complete
  - Rollback plan documented
  - Testing checklist included
- Testing: Manual review of documentation

### Phase 9: Service Registry & Deployment (depends on: Phase 8)

Register with platform and prepare for deployment.

#### Subphase 9.1: Service Registry (depends on: 8.2)

**Task 9.1.1: Implement service registration**
- Dependencies: 8.2.3
- Actions:
  - Create management command: register_service
  - Call AUTHinator /api/services/register/
  - Include service metadata (name, description, ui_url, icon)
  - Use SERVICE_REGISTRATION_KEY
  - Run on application startup
- Acceptance Criteria:
  - USERinator registers with AUTHinator
  - Service appears in registry
  - Registration on startup works
- Testing: Service registration tests

**Task 9.1.2: Add health check endpoint**
- Dependencies: 8.2.3
- Actions:
  - Create /api/users/health/ endpoint
  - Return {status: 'healthy', timestamp, version}
  - No authentication required
  - Check database connectivity
- Acceptance Criteria:
  - Health endpoint returns 200 OK
  - Includes service metadata
  - Database check included
- Testing: Health check tests

#### Subphase 9.2: Deployment Configuration (depends on: 9.1)

**Task 9.2.1: Create deployment documentation**
- Dependencies: 9.1.2
- Actions:
  - Create docs/DEPLOYMENT.md
  - Document DEPLOY_DOMAIN configuration
  - Document environment variables
  - Document Cloudflare Tunnel setup (if used)
  - Document production checklist
- Acceptance Criteria:
  - Deployment guide complete
  - Production checklist included
  - External domain setup documented
- Testing: Manual review of documentation

**Task 9.2.2: Configure production settings**
- Dependencies: 9.2.1
- Actions:
  - Set DEBUG=False for production
  - Configure ALLOWED_HOSTS from DEPLOY_DOMAIN
  - Set CSRF_COOKIE_SECURE=True for HTTPS
  - Set SESSION_COOKIE_SECURE=True for HTTPS
  - Configure production email backend
- Acceptance Criteria:
  - Production settings secure
  - HTTPS enforced
  - Email configured
- Testing: Test with DEPLOY_DOMAIN set

**Task 9.2.3: Update platform Caddyfile**
- Dependencies: 9.2.2
- Actions:
  - Add USERinator backend route to Caddyfile
  - Proxy /api/users/* to localhost:8004
  - Add caching headers for profile data
  - Test unified gateway routing
- Acceptance Criteria:
  - Caddy routes /api/users/ to USERinator
  - All services accessible through :8080
  - Caching headers applied
- Testing: Test via unified gateway

### Phase 10: Documentation & Polish (depends on: Phase 9)

Complete documentation and final quality checks.

#### Subphase 10.1: Documentation (depends on: 9.2)

**Task 10.1.1: Create comprehensive README**
- Dependencies: 9.2.3
- Actions:
  - Create README.md following INATOR.md section 7.1
  - Include project description and purpose
  - Document tech stack and versions
  - Provide quick start guide with Taskfile
  - Document API overview
  - Include testing instructions
- Acceptance Criteria:
  - README complete per INATOR.md requirements
  - Quick start guide works
  - All sections included
- Testing: Follow README to set up project

**Task 10.1.2: Generate API documentation**
- Dependencies: 9.2.3
- Actions:
  - Add drf-spectacular to requirements.txt
  - Configure OpenAPI schema generation
  - Generate API documentation
  - Host at /api/users/docs/
- Acceptance Criteria:
  - OpenAPI schema generated
  - Interactive API docs available
  - All endpoints documented
- Testing: Review API docs for completeness

**Task 10.1.3: Create architecture diagrams**
- Dependencies: 9.2.3
- Actions:
  - Create system context diagram
  - Create data model ERD
  - Create authentication flow diagram
  - Create invitation workflow diagram
  - Include in docs/ARCHITECTURE.md
- Acceptance Criteria:
  - All diagrams created
  - Architecture document complete
  - Diagrams match implementation
- Testing: Manual review of diagrams

#### Subphase 10.2: Quality Checks (depends on: 10.1)

**Task 10.2.1: Run full quality gate**
- Dependencies: 10.1.3
- Actions:
  - Run `task check` (fmt, lint, test:coverage)
  - Verify ≥85% test coverage overall
  - Verify ≥85% coverage per module
  - Fix any linting errors
  - Fix any formatting issues
- Acceptance Criteria:
  - `task check` passes without errors
  - All coverage thresholds met
  - No linting warnings
- Testing: Run task check, review output

**Task 10.2.2: Performance testing**
- Dependencies: 10.1.3
- Actions:
  - Test profile API response times (<100ms p95)
  - Test company query performance
  - Test batch profile endpoint with 100 users
  - Verify database query optimization
  - Profile slow queries
- Acceptance Criteria:
  - All endpoints meet performance targets
  - No N+1 queries
  - Database indexes used
- Testing: Performance test suite with profiling

**Task 10.2.3: Security audit**
- Dependencies: 10.1.3
- Actions:
  - Verify company scoping prevents cross-company access
  - Test privilege escalation prevention
  - Verify CSRF protection enabled
  - Check for SQL injection vulnerabilities
  - Review authentication flow security
- Acceptance Criteria:
  - No security vulnerabilities found
  - All access control tests pass
  - CSRF tokens required
- Testing: Security test suite, manual penetration testing

#### Subphase 10.3: Final Integration Testing (depends on: 10.2)

**Task 10.3.1: End-to-end platform test**
- Dependencies: 10.2.3
- Actions:
  - Start all services (AUTHinator, USERinator, RMAinator, FULFILinator)
  - Test full user journey:
    1. Admin creates company in USERinator
    2. User requests invitation in USERinator
    3. Admin approves invitation
    4. User sets password via AUTHinator
    5. User logs in, JWT includes role_level
    6. User accesses RMAinator, profile loaded from USERinator
    7. User creates RMA (permission check via role_level)
    8. Admin views all RMAs (permission check via role_level)
  - Verify caching works
  - Verify cross-service communication
- Acceptance Criteria:
  - Full user journey works end-to-end
  - All services communicate correctly
  - No errors in logs
- Testing: Manual E2E test of full platform

**Task 10.3.2: Create demo database**
- Dependencies: 10.3.1
- Actions:
  - Create management command: setup_demo_data
  - Create 3 demo companies
  - Create 10 demo users across companies
  - Assign various roles (ADMIN, MANAGER, MEMBER)
  - Create sample invitations (pending, approved, rejected)
  - Idempotent command for repeated runs
- Acceptance Criteria:
  - Demo data command works
  - Realistic sample data created
  - Can be run multiple times safely
- Testing: Run demo setup, verify data

**Task 10.3.3: Final code review**
- Dependencies: 10.3.2
- Actions:
  - Review all code for INATOR.md compliance
  - Verify all MUST requirements met
  - Check for anti-patterns
  - Verify documentation completeness
  - Create final checklist
- Acceptance Criteria:
  - All INATOR.md requirements met
  - No anti-patterns found
  - Documentation complete
- Testing: Manual code review with checklist

## Testing Strategy

### Test Coverage Requirements

Following INATOR.md section 6.1:
- MUST achieve ≥85% overall coverage
- MUST achieve ≥85% coverage per module (users/, companies/, roles/, invitations/)
- MUST test all authentication/authorization logic
- MUST test model methods and properties
- MUST test API endpoints
- SHOULD test serializer validation

### Test Categories

#### Unit Tests
- Model tests (properties, constraints, relationships)
- Serializer tests (validation, to_representation)
- Permission class tests (role_level checks)
- Utility function tests

#### Integration Tests
- API endpoint tests (CRUD operations)
- Authentication flow tests
- Cross-service communication tests (with mocked AUTHinator)
- Database transaction tests

#### E2E Tests
- User profile update flow
- Company management flow
- Invitation approval workflow
- Role assignment and permission checks
- Multi-service integration (login → USERinator → RMAinator)

### Test Execution

```bash
# Run all tests
task test

# Run with coverage
task backend:test:coverage  # Must be ≥85%
task frontend:test:coverage # Must be ≥85%

# Run E2E tests
npm run test:e2e

# Pre-commit checks
task check  # fmt + lint + test:coverage
```

### Continuous Testing

Following Deft TDD approach:
1. Write test first (red)
2. Implement minimal code to pass (green)
3. Refactor (clean)
4. Verify coverage threshold
5. Commit only when tests pass

## Deployment

### Environment Configuration

#### Backend Environment Variables

```bash
# Security
SECRET_KEY=<generate-strong-key>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# External domain
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

#### Frontend Environment Variables

```bash
VITE_DEPLOY_DOMAIN=www.example.com
```

### Deployment Checklist

- [ ] Set DEBUG=False
- [ ] Use strong SECRET_KEY
- [ ] Configure DEPLOY_DOMAIN and DEPLOY_SCHEME
- [ ] Set CSRF_COOKIE_SECURE=True
- [ ] Set SESSION_COOKIE_SECURE=True
- [ ] Configure production database (PostgreSQL)
- [ ] Configure production email backend
- [ ] Run database migrations
- [ ] Run `task setup_demo_data` (optional)
- [ ] Register service with AUTHinator
- [ ] Update Caddyfile with USERinator route
- [ ] Restart Caddy gateway
- [ ] Verify health check endpoint
- [ ] Test via unified gateway (:8080)
- [ ] Monitor logs for errors

### Port Configuration

Following INATOR.md section 4.3:
- Backend: 8004
- Unified Frontend (Vite): 5173
- Unified Gateway (Caddy): 8080

### Service Discovery

USERinator registers with AUTHinator service registry on startup:
- Name: "USERinator"
- Description: "User & company management"
- UI URL: "http://localhost:8080/users"
- Icon: "users"
- Port: 8004

## Interview Summary

### Questions Asked and Answers Given

1. **User Profile Scope**: Standard Profile (display name, avatar, phone, timezone, bio, job title, department, location) + company field for grouping
2. **Organization Structure**: Flat Organizations (each user belongs to one company, no hierarchy)
3. **Information Sharing**: Company-Scoped visibility (users only see profiles within their own company, admins see all)
4. **User Data Migration**: Stub User Model pattern (USERinator has full profiles, AUTHinator keeps stub)
5. **Company Management**: Admin-Only Creation (only platform admins can create companies)
6. **Company Metadata**: Extended Metadata (name, business info, custom_fields, tags, notes, account_status)
7. **User Roles**: USERinator manages all roles (clarified: AUTHinator queries USERinator, includes role in JWT)
8. **Role System**: Admin-Configurable Levels (default roles with numeric levels, admins can create custom roles)
9. **Role Level System**: Admin-Configurable Levels (ADMIN=100, MANAGER=30, MEMBER=10, custom roles allowed)
10. **User Preferences**: Basic Preferences (timezone, language, notification settings)
11. **API Access**: REST + Caching (other services cache user/company data with 5-15min TTL)
12. **User Onboarding**: Approval Workflow (user requests to join company → admin approves → account activated)
13. **AUTHinator Integration**: Phased Migration (build USERinator → migrate data → update AUTHinator → update other inators)
14. **Testing Strategy**: Unit + Integration + E2E Tests (comprehensive coverage ≥85%)

---

**Next Steps:**

To implement USERinator, type: `implement SPECIFICATION.md`

This will execute the phased implementation plan following Deft and INATOR.md standards.

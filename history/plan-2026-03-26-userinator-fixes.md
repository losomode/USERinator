# Userinator Fixes — 2026-03-26

## Problem
Multiple Userinator pages were broken or missing features across Profile, My Company, Companies, All Users, and Invitations tabs.

## Root Causes Found

### CompanyCreateSerializer missing `id` field
The serializer for `POST /companies/` didn't include `id` in its output, so after creating a company the frontend navigated to `/companies/undefined`.

### CompanyPage edit button hardcoded to `/company/edit`
When viewing any company via `/companies/:id`, clicking "Edit Company" navigated to `/company/edit` which calls `getMy()` — that always fails for admins (no company) and always edits the wrong company (user's own company, not the one being viewed).

### No `/companies/:id/edit` route
The route simply didn't exist in App.tsx.

### CompanyEditPage always used `getMy()`
Regardless of context, always loaded the user's own company instead of the one being edited.

### Admin "My Company" shows error
Admins have no company. `getMy()` returns 404 which was rendered as "Failed to load company."

### Invitation flow completely broken
`_coordinate_with_authinator` called `POST /api/auth/create-user/` which did not exist in AUTHinator, so approval silently failed, no user profile was created, and no email was sent.

### InvitationRequestPage had no success feedback
After submission it navigated to the same page (blank), making users think nothing happened. Duplicate submissions threw errors.

### No change-password / change-username
These AUTHinator endpoints didn't exist.

### No Create User, company filter, or delete user in All Users
These admin capabilities were missing from the frontend and backend.

## Changes Made

### AUTHinator (`Authinator/backend/`)
- **New** `auth_core/admin_views.py`: `change_password`, `change_username`, `create_user`, `set_user_password`
- **Updated** `config/urls.py`: registered all four new endpoints

### USERinator Backend (`Userinator/backend/`)
- `companies/serializers.py`: Added `id`, `account_status`, `created_at` as read-only fields to `CompanyCreateSerializer`
- `users/views.py`: Added `?company=X` filter (admin only) to UserProfileListCreateView; auto-sync username/email from AUTHinator token in `UserProfileMeView._get_profile()`
- `invitations/views.py`: Rewrote `_coordinate_with_authinator` to call new AUTHinator endpoint, derive username from email, create UserProfile via `get_or_create`, send welcome email with credentials. Added `_send_credentials_email` helper.

### USERinator Frontend (`Userinator/frontend/src/`)
- `types.ts`: Added `CreateUserProfileInput`, `CreateAuthUserInput`, `CreatedAuthUser`
- `api.ts`: Added `usersApi.delete`, `usersApi.create`, and new `authApi` module
- `pages/ProfilePage.tsx`: Added "Change Password" and "Change Username" buttons with inline modals
- `pages/CompanyPage.tsx`: Fixed edit button to use correct link per route context; graceful admin no-company message; added company users list section; added address/billing fields to display
- `pages/CompanyEditPage.tsx`: Now accepts optional `:id` param; uses `get(id)` or `getMy()` accordingly; Cancel/Save navigate back to correct page
- `pages/UserList.tsx`: Company filter dropdown (admin), "Create User" button (admin), "Remove" button per row (admin)
- **New** `pages/UserCreatePage.tsx`: Two-step user creation (AUTHinator + USERinator) with temp-password success screen
- `pages/UserEditPage.tsx`: Added "Set Password" section for admin
- `pages/InvitationRequestPage.tsx`: Success banner, better UX text ("Invite New User"), error detail from API
- `App.tsx`: Added `/users/new`, `/companies/:id/edit` routes; imported `UserCreatePage`; updated nav label

## Workflow Clarification (Invitations)
The invitation flow is admin/manager-initiated: an existing user submits an invitation for a new email → a company admin reviews and approves → AUTHinator creates a verified account with a temp password → USERinator creates the profile → the new user receives an email with their credentials and is encouraged to change their password. This is distinct from the self-registration flow in AUTHinator (`/register` → pending → admin approve).

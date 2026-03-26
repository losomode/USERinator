/** Convert SCREAMING_SNAKE_CASE role names to Title Case: PLATFORM_ADMIN → Platform Admin */
export function formatRoleName(name: string): string {
  return name
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

/** User profile — mirrors Django UserProfile model. */
export interface UserProfile {
  user_id: number;
  username: string;
  email: string;
  company: number | { id: number; name: string } | null;
  company_name?: string | null;
  display_name: string;
  avatar_url: string;
  phone: string;
  bio: string;
  job_title: string;
  department: string;
  location: string;
  role_name: string;
  role_level: number;
  timezone: string;
  language: string;
  notification_email: boolean;
  notification_in_app: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Fields editable by the user themselves. */
export interface UpdateProfileInput {
  display_name?: string;
  avatar_url?: string;
  phone?: string;
  bio?: string;
  job_title?: string;
  department?: string;
  location?: string;
  timezone?: string;
  language?: string;
  notification_email?: boolean;
  notification_in_app?: boolean;
}

/** Company from USERinator /api/companies/ */
export interface Company {
  id: number;
  name: string;
  address: string;
  phone: string;
  website: string;
  industry: string;
  company_size: string;
  logo_url: string;
  billing_contact_email: string;
  custom_fields: Record<string, unknown>;
  tags: string[];
  notes: string;
  account_status: string;
  created_at: string;
  user_count?: number;
}

/** Fields editable on a company. */
export interface UpdateCompanyInput {
  name?: string;
  address?: string;
  phone?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  logo_url?: string;
  billing_contact_email?: string;
  custom_fields?: Record<string, unknown>;
  tags?: string[];
  notes?: string;
  account_status?: string;
}

/** Role definition. */
export interface Role {
  id: number;
  role_name: string;
  role_level: number;
  description: string;
  is_system_role: boolean;
  created_at: string;
}

/** User invitation from USERinator /api/invitations/ */
export interface Invitation {
  id: number;
  email: string;
  company: number;
  company_name?: string;
  requested_role: number;
  requested_role_name?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  requested_at: string;
  message: string;
  reviewed_at: string | null;
  review_notes: string;
  expires_at: string;
}

/** Input for creating a company (platform admin). */
export interface CreateCompanyInput {
  name: string;
  address?: string;
  phone?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  logo_url?: string;
  billing_contact_email?: string;
  custom_fields?: Record<string, unknown>;
  tags?: string[];
  notes?: string;
}

/** Input for creating an invitation. */
export interface CreateInvitationInput {
  email: string;
  company: number;
  requested_role: number;
  message?: string;
}

/** Input for creating a USERinator profile (admin-only). */
export interface CreateUserProfileInput {
  user_id: number;
  username: string;
  email: string;
  company: number;
  display_name?: string;
  role_name: string;
  role_level: number;
}

/** Input for creating an AUTHinator auth user. */
export interface CreateAuthUserInput {
  email: string;
  username: string;
  role?: 'ADMIN' | 'USER';
  temp_password?: string;
}

/** Response from AUTHinator create-user endpoint. */
export interface CreatedAuthUser {
  id: number;
  username: string;
  email: string;
  temp_password: string;
}

/** User preferences subset. */
export interface UserPreferences {
  timezone: string;
  language: string;
  notification_email: boolean;
  notification_in_app: boolean;
}

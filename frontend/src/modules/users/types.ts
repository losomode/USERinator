/** User profile — mirrors Django UserProfile model. */
export interface UserProfile {
  user_id: number;
  username: string;
  email: string;
  company: number;
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

/** Company — mirrors Django Company model. */
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
}

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

/** User invitation. */
export interface Invitation {
  id: number;
  email: string;
  company: number;
  requested_role: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED';
  requested_at: string;
  message: string;
  reviewed_at: string | null;
  review_notes: string;
  expires_at: string;
}

export interface CreateInvitationInput {
  email: string;
  company: number;
  requested_role: number;
  message?: string;
}

/** User preferences (subset of UserProfile). */
export interface Preferences {
  timezone: string;
  language: string;
  notification_email: boolean;
  notification_in_app: boolean;
}

/** Paginated response from DRF. */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

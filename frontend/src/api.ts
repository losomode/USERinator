import apiClient from '@inator/shared/api/client';
import type {
  UserProfile,
  UpdateProfileInput,
  CreateUserProfileInput,
  Company,
  UpdateCompanyInput,
  CreateCompanyInput,
  Role,
  Invitation,
  CreateInvitationInput,
  UserPreferences,
  CreateAuthUserInput,
  CreatedAuthUser,
} from './types';

/** Paginated response from DRF. */
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** User profile endpoints. */
export const usersApi = {
  list: async (params?: Record<string, string>): Promise<UserProfile[]> => {
    const response = await apiClient.get<PaginatedResponse<UserProfile>>('/users/', { params });
    return response.data.results;
  },

  get: async (userId: number): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>(`/users/${String(userId)}/`);
    return response.data;
  },

  me: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>('/users/me/');
    return response.data;
  },

  updateMe: async (data: UpdateProfileInput): Promise<UserProfile> => {
    const response = await apiClient.patch<UserProfile>('/users/me/', data);
    return response.data;
  },

  update: async (userId: number, data: Partial<UserProfile>): Promise<UserProfile> => {
    const response = await apiClient.patch<UserProfile>(`/users/${String(userId)}/`, data);
    return response.data;
  },

  delete: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${String(userId)}/`);
  },

  deactivate: async (userId: number): Promise<void> => {
    await apiClient.post(`/users/${String(userId)}/deactivate/`);
  },

  markForDeletion: async (userId: number): Promise<void> => {
    await apiClient.post(`/users/${String(userId)}/mark-for-deletion/`);
  },

  setCredentials: async (
    userId: number,
    data: { password?: string; new_username?: string },
  ): Promise<{ detail: string }> => {
    const response = await apiClient.post<{ detail: string }>(
      `/users/${String(userId)}/set-credentials/`,
      data,
    );
    return response.data;
  },

  create: async (data: CreateUserProfileInput): Promise<UserProfile> => {
    const response = await apiClient.post<UserProfile>('/users/', data);
    return response.data;
  },

  batch: async (userIds: number[]): Promise<UserProfile[]> => {
    const response = await apiClient.post<UserProfile[]>('/users/batch/', { user_ids: userIds });
    return response.data;
  },
};

/** AUTHinator endpoints (called via /api/auth/ through the Caddy gateway). */
export const authApi = {
  changePassword: async (data: { current_password: string; new_password: string }): Promise<void> => {
    await apiClient.post('/auth/change-password/', data);
  },

  changeUsername: async (data: { new_username: string; password: string }): Promise<{ username: string }> => {
    const response = await apiClient.post<{ username: string }>('/auth/change-username/', data);
    return response.data;
  },

  createUser: async (data: CreateAuthUserInput): Promise<CreatedAuthUser> => {
    const response = await apiClient.post<CreatedAuthUser>('/auth/create-user/', data);
    return response.data;
  },

  setUserPassword: async (data: { user_id: number; new_password: string }): Promise<void> => {
    await apiClient.post('/auth/admin/set-password/', data);
  },
};

/** Company endpoints. */
export const companiesApi = {
  list: async (): Promise<Company[]> => {
    const response = await apiClient.get<PaginatedResponse<Company>>('/companies/');
    return response.data.results;
  },

  get: async (id: number): Promise<Company> => {
    const response = await apiClient.get<Company>(`/companies/${String(id)}/`);
    return response.data;
  },

  getMy: async (): Promise<Company> => {
    const response = await apiClient.get<Company>('/companies/my/');
    return response.data;
  },

  update: async (id: number, data: UpdateCompanyInput): Promise<Company> => {
    const response = await apiClient.patch<Company>(`/companies/${String(id)}/`, data);
    return response.data;
  },

  create: async (data: CreateCompanyInput): Promise<Company> => {
    const response = await apiClient.post<Company>('/companies/', data);
    return response.data;
  },

  getUsers: async (id: number): Promise<UserProfile[]> => {
    const response = await apiClient.get<PaginatedResponse<UserProfile>>(`/companies/${String(id)}/users/`);
    return response.data.results;
  },
};

/** Role endpoints. */
export const rolesApi = {
  list: async (): Promise<Role[]> => {
    const response = await apiClient.get<PaginatedResponse<Role>>('/roles/');
    return response.data.results;
  },
};

/** Invitation endpoints. */
export const invitationsApi = {
  list: async (params?: Record<string, string>): Promise<Invitation[]> => {
    const response = await apiClient.get<PaginatedResponse<Invitation>>('/invitations/', { params });
    return response.data.results;
  },

  create: async (data: CreateInvitationInput): Promise<Invitation & { provisioned_user?: { username: string; temp_password: string; note: string } | null; provision_error?: string }> => {
    const response = await apiClient.post<Invitation & { provisioned_user?: { username: string; temp_password: string; note: string } | null; provision_error?: string }>('/invitations/', data);
    return response.data;
  },

  approve: async (id: number, reviewNotes?: string): Promise<Invitation & { provisioned_user?: unknown; provision_error?: string }> => {
    const response = await apiClient.post<Invitation & { provisioned_user?: unknown; provision_error?: string }>(`/invitations/${String(id)}/approve/`, {
      review_notes: reviewNotes ?? '',
    });
    return response.data;
  },

  reject: async (id: number, reviewNotes?: string): Promise<Invitation> => {
    const response = await apiClient.post<Invitation>(`/invitations/${String(id)}/reject/`, {
      review_notes: reviewNotes ?? '',
    });
    return response.data;
  },
};

/** User preferences endpoints. */
export const preferencesApi = {
  get: async (): Promise<UserPreferences> => {
    const response = await apiClient.get<UserPreferences>('/users/preferences/me/');
    return response.data;
  },

  update: async (data: Partial<UserPreferences>): Promise<UserPreferences> => {
    const response = await apiClient.patch<UserPreferences>('/users/preferences/me/', data);
    return response.data;
  },
};

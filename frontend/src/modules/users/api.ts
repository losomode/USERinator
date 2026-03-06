import apiClient from '../../shared/api/client';
import type {
  UserProfile,
  UpdateProfileInput,
  Company,
  UpdateCompanyInput,
  Role,
  Invitation,
  CreateInvitationInput,
  Preferences,
  PaginatedResponse,
} from './types';

export const userApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get<PaginatedResponse<UserProfile>>('/users/', { params });
    return response.data;
  },

  get: async (userId: number) => {
    const response = await apiClient.get<UserProfile>(`/users/${userId}/`);
    return response.data;
  },

  getMe: async () => {
    const response = await apiClient.get<UserProfile>('/users/me/');
    return response.data;
  },

  updateMe: async (data: UpdateProfileInput) => {
    const response = await apiClient.patch<UserProfile>('/users/me/', data);
    return response.data;
  },

  batch: async (userIds: number[]) => {
    const response = await apiClient.post<UserProfile[]>('/users/batch/', { user_ids: userIds });
    return response.data;
  },
};

export const companyApi = {
  list: async () => {
    const response = await apiClient.get<PaginatedResponse<Company>>('/companies/');
    return response.data;
  },

  get: async (id: number) => {
    const response = await apiClient.get<Company>(`/companies/${id}/`);
    return response.data;
  },

  getMy: async () => {
    const response = await apiClient.get<Company>('/companies/my/');
    return response.data;
  },

  update: async (id: number, data: UpdateCompanyInput) => {
    const response = await apiClient.patch<Company>(`/companies/${id}/`, data);
    return response.data;
  },

  getUsers: async (id: number) => {
    const response = await apiClient.get<PaginatedResponse<UserProfile>>(`/companies/${id}/users/`);
    return response.data;
  },
};

export const roleApi = {
  list: async () => {
    const response = await apiClient.get<PaginatedResponse<Role>>('/roles/');
    return response.data;
  },
};

export const invitationApi = {
  list: async (params?: Record<string, unknown>) => {
    const response = await apiClient.get<PaginatedResponse<Invitation>>('/invitations/', { params });
    return response.data;
  },

  create: async (data: CreateInvitationInput) => {
    const response = await apiClient.post<Invitation>('/invitations/', data);
    return response.data;
  },

  approve: async (id: number, reviewNotes?: string) => {
    const response = await apiClient.post<Invitation>(`/invitations/${id}/approve/`, {
      review_notes: reviewNotes ?? '',
    });
    return response.data;
  },

  reject: async (id: number, reviewNotes?: string) => {
    const response = await apiClient.post<Invitation>(`/invitations/${id}/reject/`, {
      review_notes: reviewNotes ?? '',
    });
    return response.data;
  },
};

export const preferencesApi = {
  get: async () => {
    const response = await apiClient.get<Preferences>('/users/preferences/me/');
    return response.data;
  },

  update: async (data: Partial<Preferences>) => {
    const response = await apiClient.patch<Preferences>('/users/preferences/me/', data);
    return response.data;
  },
};

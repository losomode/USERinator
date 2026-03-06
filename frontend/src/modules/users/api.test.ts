import { describe, it, expect, vi, beforeEach } from 'vitest';
import { userApi, companyApi, roleApi, invitationApi, preferencesApi } from './api';
import apiClient from '../../shared/api/client';

vi.mock('../../shared/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

const mock = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('userApi', () => {
  it('list fetches paginated users', async () => {
    const data = { count: 1, results: [{ user_id: 1 }] };
    mock.get.mockResolvedValue({ data });
    const result = await userApi.list({ search: 'bob' });
    expect(mock.get).toHaveBeenCalledWith('/users/', { params: { search: 'bob' } });
    expect(result).toEqual(data);
  });

  it('get fetches user by id', async () => {
    const data = { user_id: 5 };
    mock.get.mockResolvedValue({ data });
    const result = await userApi.get(5);
    expect(mock.get).toHaveBeenCalledWith('/users/5/');
    expect(result).toEqual(data);
  });

  it('getMe fetches current user profile', async () => {
    const data = { user_id: 1 };
    mock.get.mockResolvedValue({ data });
    const result = await userApi.getMe();
    expect(mock.get).toHaveBeenCalledWith('/users/me/');
    expect(result).toEqual(data);
  });

  it('updateMe patches profile', async () => {
    const data = { user_id: 1, display_name: 'New' };
    mock.patch.mockResolvedValue({ data });
    const result = await userApi.updateMe({ display_name: 'New' });
    expect(mock.patch).toHaveBeenCalledWith('/users/me/', { display_name: 'New' });
    expect(result).toEqual(data);
  });

  it('batch posts user ids', async () => {
    const data = [{ user_id: 1 }, { user_id: 2 }];
    mock.post.mockResolvedValue({ data });
    const result = await userApi.batch([1, 2]);
    expect(mock.post).toHaveBeenCalledWith('/users/batch/', { user_ids: [1, 2] });
    expect(result).toEqual(data);
  });
});

describe('companyApi', () => {
  it('list fetches companies', async () => {
    const data = { count: 1, results: [] };
    mock.get.mockResolvedValue({ data });
    const result = await companyApi.list();
    expect(mock.get).toHaveBeenCalledWith('/companies/');
    expect(result).toEqual(data);
  });

  it('get fetches company by id', async () => {
    const data = { id: 3 };
    mock.get.mockResolvedValue({ data });
    const result = await companyApi.get(3);
    expect(mock.get).toHaveBeenCalledWith('/companies/3/');
    expect(result).toEqual(data);
  });

  it('getMy fetches current user company', async () => {
    const data = { id: 1 };
    mock.get.mockResolvedValue({ data });
    const result = await companyApi.getMy();
    expect(mock.get).toHaveBeenCalledWith('/companies/my/');
    expect(result).toEqual(data);
  });

  it('update patches company', async () => {
    const data = { id: 1, name: 'Updated' };
    mock.patch.mockResolvedValue({ data });
    const result = await companyApi.update(1, { name: 'Updated' });
    expect(mock.patch).toHaveBeenCalledWith('/companies/1/', { name: 'Updated' });
    expect(result).toEqual(data);
  });

  it('getUsers fetches company users', async () => {
    const data = { count: 2, results: [] };
    mock.get.mockResolvedValue({ data });
    const result = await companyApi.getUsers(1);
    expect(mock.get).toHaveBeenCalledWith('/companies/1/users/');
    expect(result).toEqual(data);
  });
});

describe('roleApi', () => {
  it('list fetches roles', async () => {
    const data = { count: 2, results: [{ id: 1 }] };
    mock.get.mockResolvedValue({ data });
    const result = await roleApi.list();
    expect(mock.get).toHaveBeenCalledWith('/roles/');
    expect(result).toEqual(data);
  });
});

describe('invitationApi', () => {
  it('list fetches invitations with params', async () => {
    const data = { count: 0, results: [] };
    mock.get.mockResolvedValue({ data });
    const result = await invitationApi.list({ status: 'PENDING' });
    expect(mock.get).toHaveBeenCalledWith('/invitations/', { params: { status: 'PENDING' } });
    expect(result).toEqual(data);
  });

  it('create posts invitation', async () => {
    const input = { email: 'a@b.com', company: 1, requested_role: 2 };
    const data = { id: 10, ...input };
    mock.post.mockResolvedValue({ data });
    const result = await invitationApi.create(input);
    expect(mock.post).toHaveBeenCalledWith('/invitations/', input);
    expect(result).toEqual(data);
  });

  it('approve posts approval', async () => {
    const data = { id: 10, status: 'APPROVED' };
    mock.post.mockResolvedValue({ data });
    const result = await invitationApi.approve(10, 'looks good');
    expect(mock.post).toHaveBeenCalledWith('/invitations/10/approve/', { review_notes: 'looks good' });
    expect(result).toEqual(data);
  });

  it('approve posts with empty notes when none provided', async () => {
    const data = { id: 10, status: 'APPROVED' };
    mock.post.mockResolvedValue({ data });
    await invitationApi.approve(10);
    expect(mock.post).toHaveBeenCalledWith('/invitations/10/approve/', { review_notes: '' });
  });

  it('reject posts rejection', async () => {
    const data = { id: 10, status: 'REJECTED' };
    mock.post.mockResolvedValue({ data });
    const result = await invitationApi.reject(10, 'no');
    expect(mock.post).toHaveBeenCalledWith('/invitations/10/reject/', { review_notes: 'no' });
    expect(result).toEqual(data);
  });

  it('reject posts with empty notes when none provided', async () => {
    const data = { id: 10, status: 'REJECTED' };
    mock.post.mockResolvedValue({ data });
    await invitationApi.reject(10);
    expect(mock.post).toHaveBeenCalledWith('/invitations/10/reject/', { review_notes: '' });
  });
});

describe('preferencesApi', () => {
  it('get fetches preferences', async () => {
    const data = { timezone: 'UTC', language: 'en' };
    mock.get.mockResolvedValue({ data });
    const result = await preferencesApi.get();
    expect(mock.get).toHaveBeenCalledWith('/users/preferences/me/');
    expect(result).toEqual(data);
  });

  it('update patches preferences', async () => {
    const data = { timezone: 'US/Eastern', language: 'en' };
    mock.patch.mockResolvedValue({ data });
    const result = await preferencesApi.update({ timezone: 'US/Eastern' });
    expect(mock.patch).toHaveBeenCalledWith('/users/preferences/me/', { timezone: 'US/Eastern' });
    expect(result).toEqual(data);
  });
});

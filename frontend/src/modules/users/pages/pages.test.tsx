import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../../../test/helpers';
import { ProfilePage } from './ProfilePage';
import { ProfileEditPage } from './ProfileEditPage';
import { UserListPage } from './UserListPage';
import { CompanyPage } from './CompanyPage';
import { CompanyEditPage } from './CompanyEditPage';
import { InvitationReviewPage } from './InvitationReviewPage';
import { InvitationRequestPage } from './InvitationRequestPage';
import { PreferencesPage } from './PreferencesPage';

// ── Hoisted mocks (vi.mock factories are hoisted, so variables must be too) ──
const { mockUserApi, mockCompanyApi, mockInvitationApi, mockRoleApi, mockPreferencesApi, mockNavigate, mockAuth } = vi.hoisted(() => ({
  mockUserApi: { getMe: vi.fn(), updateMe: vi.fn(), list: vi.fn() },
  mockCompanyApi: { getMy: vi.fn(), update: vi.fn(), list: vi.fn() },
  mockInvitationApi: { list: vi.fn(), create: vi.fn(), approve: vi.fn(), reject: vi.fn() },
  mockRoleApi: { list: vi.fn() },
  mockPreferencesApi: { get: vi.fn(), update: vi.fn() },
  mockNavigate: vi.fn(),
  mockAuth: {
    user: { id: 1, username: 'testuser', email: 'test@test.com', role: 'admin', role_level: 100, company_id: 1 },
    isAdmin: true,
    isCompanyAdmin: true,
    login: vi.fn(),
    logout: vi.fn(),
    loading: false,
  },
}));

vi.mock('../../../shared/auth/AuthProvider', () => ({
  useAuth: () => mockAuth,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../api', () => ({
  userApi: mockUserApi,
  companyApi: mockCompanyApi,
  invitationApi: mockInvitationApi,
  roleApi: mockRoleApi,
  preferencesApi: mockPreferencesApi,
}));

// ── Fixtures ──
const profileFixture = {
  user_id: 1,
  username: 'jdoe',
  email: 'jdoe@example.com',
  display_name: 'John Doe',
  phone: '555-1234',
  bio: 'A bio',
  job_title: 'Engineer',
  department: 'Eng',
  location: 'NYC',
  role_name: 'Admin',
  role_level: 100,
  avatar_url: '',
  company: 1,
  timezone: 'UTC',
  language: 'en',
  notification_email: true,
  notification_in_app: false,
  is_active: true,
  created_at: '2024-01-01',
  updated_at: '2024-01-02',
};

const companyFixture = {
  id: 1,
  name: 'Acme Corp',
  address: '123 Main St',
  phone: '555-0000',
  website: 'https://acme.com',
  industry: 'Tech',
  company_size: '50-100',
  logo_url: '',
  billing_contact_email: 'billing@acme.com',
  custom_fields: {},
  tags: ['vip', 'enterprise'],
  notes: '',
  account_status: 'active',
  created_at: '2024-01-01',
};

const invitationFixture = {
  id: 1,
  email: 'new@example.com',
  company: 1,
  requested_role: 2,
  status: 'PENDING' as const,
  requested_at: '2024-06-01T00:00:00Z',
  message: 'Please add me',
  reviewed_at: null,
  review_notes: '',
  expires_at: '2024-07-01T00:00:00Z',
};

const prefsFixture = {
  timezone: 'UTC',
  language: 'en',
  notification_email: true,
  notification_in_app: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  mockNavigate.mockReset();
});

// ════════════════════════════════════════════════════
// ProfilePage
// ════════════════════════════════════════════════════
describe('ProfilePage', () => {
  it('renders profile data after load', async () => {
    mockUserApi.getMe.mockResolvedValue(profileFixture);
    renderWithRouter(<ProfilePage />);

    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('John Doe')).toBeInTheDocument());
    expect(screen.getByText('jdoe@example.com')).toBeInTheDocument();
    expect(screen.getByText('Engineer')).toBeInTheDocument();
  });

  it('shows error on fetch failure', async () => {
    mockUserApi.getMe.mockRejectedValue(new Error('fail'));
    renderWithRouter(<ProfilePage />);

    await waitFor(() => expect(screen.getByText('Failed to load profile.')).toBeInTheDocument());
  });

  it('has edit link', async () => {
    mockUserApi.getMe.mockResolvedValue(profileFixture);
    renderWithRouter(<ProfilePage />);

    await waitFor(() => expect(screen.getByText('Edit Profile')).toBeInTheDocument());
    expect(screen.getByText('Edit Profile').closest('a')).toHaveAttribute('href', '/profile/edit');
  });
});

// ════════════════════════════════════════════════════
// ProfileEditPage
// ════════════════════════════════════════════════════
describe('ProfileEditPage', () => {
  it('loads profile and renders form', async () => {
    mockUserApi.getMe.mockResolvedValue(profileFixture);
    renderWithRouter(<ProfileEditPage />);

    await waitFor(() => expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument());
    expect(screen.getByDisplayValue('Engineer')).toBeInTheDocument();
  });

  it('submits form and navigates', async () => {
    mockUserApi.getMe.mockResolvedValue(profileFixture);
    mockUserApi.updateMe.mockResolvedValue(profileFixture);
    const user = userEvent.setup();
    renderWithRouter(<ProfileEditPage />);

    await waitFor(() => screen.getByDisplayValue('John Doe'));
    await user.click(screen.getByText('Save'));
    await waitFor(() => expect(mockUserApi.updateMe).toHaveBeenCalled());
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });

  it('shows error on save failure', async () => {
    mockUserApi.getMe.mockResolvedValue(profileFixture);
    mockUserApi.updateMe.mockRejectedValue(new Error('fail'));
    const user = userEvent.setup();
    renderWithRouter(<ProfileEditPage />);

    await waitFor(() => screen.getByDisplayValue('John Doe'));
    await user.click(screen.getByText('Save'));
    await waitFor(() => expect(screen.getByText('Failed to save profile.')).toBeInTheDocument());
  });

  it('cancel button navigates back', async () => {
    mockUserApi.getMe.mockResolvedValue(profileFixture);
    const user = userEvent.setup();
    renderWithRouter(<ProfileEditPage />);

    await waitFor(() => screen.getByDisplayValue('John Doe'));
    await user.click(screen.getByText('Cancel'));
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });
});

// ════════════════════════════════════════════════════
// UserListPage
// ════════════════════════════════════════════════════
describe('UserListPage', () => {
  it('renders user list', async () => {
    mockUserApi.list.mockResolvedValue({ count: 1, results: [profileFixture] });
    renderWithRouter(<UserListPage />);

    await waitFor(() => expect(screen.getByText('John Doe')).toBeInTheDocument());
  });

  it('shows empty state', async () => {
    mockUserApi.list.mockResolvedValue({ count: 0, results: [] });
    renderWithRouter(<UserListPage />);

    await waitFor(() => expect(screen.getByText('No users found.')).toBeInTheDocument());
  });
});

// ════════════════════════════════════════════════════
// CompanyPage
// ════════════════════════════════════════════════════
describe('CompanyPage', () => {
  it('renders company data', async () => {
    mockCompanyApi.getMy.mockResolvedValue(companyFixture);
    renderWithRouter(<CompanyPage />);

    await waitFor(() => expect(screen.getByText('Acme Corp')).toBeInTheDocument());
    expect(screen.getByText('Tech')).toBeInTheDocument();
    expect(screen.getByText('vip, enterprise')).toBeInTheDocument();
  });

  it('shows edit button for company admin', async () => {
    mockCompanyApi.getMy.mockResolvedValue(companyFixture);
    renderWithRouter(<CompanyPage />);

    await waitFor(() => expect(screen.getByText('Edit Company')).toBeInTheDocument());
  });

  it('shows error on failure', async () => {
    mockCompanyApi.getMy.mockRejectedValue(new Error('fail'));
    renderWithRouter(<CompanyPage />);

    await waitFor(() => expect(screen.getByText('Failed to load company.')).toBeInTheDocument());
  });
});

// ════════════════════════════════════════════════════
// CompanyEditPage
// ════════════════════════════════════════════════════
describe('CompanyEditPage', () => {
  it('loads company and renders form', async () => {
    mockCompanyApi.getMy.mockResolvedValue(companyFixture);
    renderWithRouter(<CompanyEditPage />);

    await waitFor(() => expect(screen.getByDisplayValue('Acme Corp')).toBeInTheDocument());
  });

  it('submits form and navigates', async () => {
    mockCompanyApi.getMy.mockResolvedValue(companyFixture);
    mockCompanyApi.update.mockResolvedValue(companyFixture);
    const user = userEvent.setup();
    renderWithRouter(<CompanyEditPage />);

    await waitFor(() => screen.getByDisplayValue('Acme Corp'));
    await user.click(screen.getByText('Save Changes'));
    await waitFor(() => expect(mockCompanyApi.update).toHaveBeenCalled());
    expect(mockNavigate).toHaveBeenCalledWith('/company');
  });

  it('shows error on save failure', async () => {
    mockCompanyApi.getMy.mockResolvedValue(companyFixture);
    mockCompanyApi.update.mockRejectedValue(new Error('fail'));
    const user = userEvent.setup();
    renderWithRouter(<CompanyEditPage />);

    await waitFor(() => screen.getByDisplayValue('Acme Corp'));
    await user.click(screen.getByText('Save Changes'));
    await waitFor(() => expect(screen.getByText('Failed to save changes.')).toBeInTheDocument());
  });

  it('shows error on load failure', async () => {
    mockCompanyApi.getMy.mockRejectedValue(new Error('fail'));
    renderWithRouter(<CompanyEditPage />);

    await waitFor(() => expect(screen.getByText('Failed to load company.')).toBeInTheDocument());
  });
});

// ════════════════════════════════════════════════════
// InvitationRequestPage
// ════════════════════════════════════════════════════
describe('InvitationRequestPage', () => {
  beforeEach(() => {
    mockRoleApi.list.mockResolvedValue({ count: 1, results: [{ id: 2, role_name: 'User' }] });
    mockCompanyApi.list.mockResolvedValue({ count: 1, results: [{ id: 1, name: 'Acme Corp' }] });
  });

  it('renders form with selects', async () => {
    renderWithRouter(<InvitationRequestPage />);

    await waitFor(() => expect(screen.getByText('Acme Corp')).toBeInTheDocument());
    expect(screen.getByText('User')).toBeInTheDocument();
  });

  it('shows validation error when company/role not selected', async () => {
    const user = userEvent.setup();
    renderWithRouter(<InvitationRequestPage />);

    await waitFor(() => screen.getByText('Acme Corp'));

    // Fill email but don't select company or role
    await user.type(screen.getByLabelText('Email'), 'test@test.com');
    // Company and role selects default to '' which won't pass the !companyId || !roleId check
    await user.click(screen.getByText('Submit Request'));
    await waitFor(() => expect(screen.getByText('Company and role are required.')).toBeInTheDocument());
  });

  it('submits successfully', async () => {
    mockInvitationApi.create.mockResolvedValue({ id: 10 });
    const user = userEvent.setup();
    renderWithRouter(<InvitationRequestPage />);

    await waitFor(() => screen.getByText('Acme Corp'));
    await user.type(screen.getByLabelText('Email'), 'new@test.com');
    await user.selectOptions(screen.getByLabelText('Company'), '1');
    await user.selectOptions(screen.getByLabelText('Requested Role'), '2');
    await user.click(screen.getByText('Submit Request'));

    await waitFor(() => expect(mockInvitationApi.create).toHaveBeenCalled());
    expect(mockNavigate).toHaveBeenCalledWith('/invitations');
  });

  it('shows error on submit failure', async () => {
    mockInvitationApi.create.mockRejectedValue(new Error('fail'));
    const user = userEvent.setup();
    renderWithRouter(<InvitationRequestPage />);

    await waitFor(() => screen.getByText('Acme Corp'));
    await user.type(screen.getByLabelText('Email'), 'new@test.com');
    await user.selectOptions(screen.getByLabelText('Company'), '1');
    await user.selectOptions(screen.getByLabelText('Requested Role'), '2');
    await user.click(screen.getByText('Submit Request'));

    await waitFor(() => expect(screen.getByText('Failed to submit invitation request.')).toBeInTheDocument());
  });
});

// ════════════════════════════════════════════════════
// InvitationReviewPage
// ════════════════════════════════════════════════════
describe('InvitationReviewPage', () => {
  it('renders pending invitations', async () => {
    mockInvitationApi.list.mockResolvedValue({ count: 1, results: [invitationFixture] });
    renderWithRouter(<InvitationReviewPage />);

    await waitFor(() => expect(screen.getByText('new@example.com')).toBeInTheDocument());
    expect(screen.getByText('Please add me')).toBeInTheDocument();
  });

  it('shows empty state', async () => {
    mockInvitationApi.list.mockResolvedValue({ count: 0, results: [] });
    renderWithRouter(<InvitationReviewPage />);

    await waitFor(() => expect(screen.getByText('No pending invitations.')).toBeInTheDocument());
  });

  it('approves invitation', async () => {
    mockInvitationApi.list.mockResolvedValue({ count: 1, results: [invitationFixture] });
    mockInvitationApi.approve.mockResolvedValue({ ...invitationFixture, status: 'APPROVED' });
    const user = userEvent.setup();
    renderWithRouter(<InvitationReviewPage />);

    await waitFor(() => screen.getByText('new@example.com'));
    await user.click(screen.getByText('Approve'));
    await waitFor(() => expect(mockInvitationApi.approve).toHaveBeenCalledWith(1, undefined));
    // Invitation removed from list
    await waitFor(() => expect(screen.queryByText('new@example.com')).not.toBeInTheDocument());
  });

  it('rejects invitation', async () => {
    mockInvitationApi.list.mockResolvedValue({ count: 1, results: [invitationFixture] });
    mockInvitationApi.reject.mockResolvedValue({ ...invitationFixture, status: 'REJECTED' });
    const user = userEvent.setup();
    renderWithRouter(<InvitationReviewPage />);

    await waitFor(() => screen.getByText('new@example.com'));
    await user.click(screen.getByText('Reject'));
    await waitFor(() => expect(mockInvitationApi.reject).toHaveBeenCalledWith(1, undefined));
  });

  it('shows error on load failure', async () => {
    mockInvitationApi.list.mockRejectedValue(new Error('fail'));
    renderWithRouter(<InvitationReviewPage />);

    await waitFor(() => expect(screen.getByText('Failed to load invitations.')).toBeInTheDocument());
  });

  it('shows error on action failure', async () => {
    mockInvitationApi.list.mockResolvedValue({ count: 1, results: [invitationFixture] });
    mockInvitationApi.approve.mockRejectedValue(new Error('fail'));
    const user = userEvent.setup();
    renderWithRouter(<InvitationReviewPage />);

    await waitFor(() => screen.getByText('new@example.com'));
    await user.click(screen.getByText('Approve'));
    await waitFor(() => expect(screen.getByText('Failed to approve invitation.')).toBeInTheDocument());
  });
});

// ════════════════════════════════════════════════════
// PreferencesPage
// ════════════════════════════════════════════════════
describe('PreferencesPage', () => {
  it('renders preferences form', async () => {
    mockPreferencesApi.get.mockResolvedValue(prefsFixture);
    renderWithRouter(<PreferencesPage />);

    await waitFor(() => expect(screen.getByDisplayValue('UTC')).toBeInTheDocument());
    expect(screen.getByDisplayValue('en')).toBeInTheDocument();
  });

  it('saves preferences and shows success', async () => {
    mockPreferencesApi.get.mockResolvedValue(prefsFixture);
    mockPreferencesApi.update.mockResolvedValue({ ...prefsFixture, timezone: 'US/Eastern' });
    const user = userEvent.setup();
    renderWithRouter(<PreferencesPage />);

    await waitFor(() => screen.getByDisplayValue('UTC'));
    await user.clear(screen.getByDisplayValue('UTC'));
    await user.type(screen.getByLabelText('Timezone'), 'US/Eastern');
    await user.click(screen.getByText('Save Preferences'));

    await waitFor(() => expect(screen.getByText('Preferences saved.')).toBeInTheDocument());
  });

  it('shows error on load failure', async () => {
    mockPreferencesApi.get.mockRejectedValue(new Error('fail'));
    renderWithRouter(<PreferencesPage />);

    await waitFor(() => expect(screen.getByText('Failed to load preferences.')).toBeInTheDocument());
  });

  it('shows error on save failure', async () => {
    mockPreferencesApi.get.mockResolvedValue(prefsFixture);
    mockPreferencesApi.update.mockRejectedValue(new Error('fail'));
    const user = userEvent.setup();
    renderWithRouter(<PreferencesPage />);

    await waitFor(() => screen.getByDisplayValue('UTC'));
    await user.click(screen.getByText('Save Preferences'));
    await waitFor(() => expect(screen.getByText('Failed to save preferences.')).toBeInTheDocument());
  });

  it('toggles checkbox and clears saved state', async () => {
    mockPreferencesApi.get.mockResolvedValue(prefsFixture);
    mockPreferencesApi.update.mockResolvedValue(prefsFixture);
    const user = userEvent.setup();
    renderWithRouter(<PreferencesPage />);

    await waitFor(() => screen.getByDisplayValue('UTC'));
    // Save first
    await user.click(screen.getByText('Save Preferences'));
    await waitFor(() => screen.getByText('Preferences saved.'));
    // Toggle checkbox — should clear "saved" message
    await user.click(screen.getByLabelText('In-app notifications'));
    expect(screen.queryByText('Preferences saved.')).not.toBeInTheDocument();
  });
});

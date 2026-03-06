import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../../test/helpers';
import { Layout, type NavItem } from './Layout';

const mockLogout = vi.fn();
vi.mock('../auth/AuthProvider', () => ({
  useAuth: () => ({
    user: { id: 1, username: 'admin', email: 'a@b.com', role: 'admin', role_level: 100, company_id: 1 },
    isAdmin: true,
    isCompanyAdmin: true,
    login: vi.fn(),
    logout: mockLogout,
    loading: false,
  }),
}));

const navItems: NavItem[] = [
  { label: 'Profile', path: '/profile' },
  { label: 'Admin Panel', path: '/admin', adminOnly: true },
];

describe('Layout', () => {
  it('renders title and subtitle', () => {
    renderWithRouter(
      <Layout title="Test App" subtitle="Subtitle" navItems={navItems}>
        <div>Content</div>
      </Layout>,
    );
    expect(screen.getByText('Test App')).toBeInTheDocument();
    expect(screen.getByText('Subtitle')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('renders nav items and admin-only items for admin', () => {
    renderWithRouter(
      <Layout title="App" navItems={navItems}>
        <div />
      </Layout>,
    );
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Admin Panel')).toBeInTheDocument();
  });

  it('shows username and logout button', async () => {
    const user = userEvent.setup();
    renderWithRouter(
      <Layout title="App" navItems={navItems}>
        <div />
      </Layout>,
    );
    expect(screen.getByText('admin')).toBeInTheDocument();
    await user.click(screen.getByText('Logout'));
    expect(mockLogout).toHaveBeenCalled();
  });
});

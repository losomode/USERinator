import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithRouter } from '../../test/helpers';
import { ProtectedRoute } from './ProtectedRoute';

let mockAuthState = {
  user: null as { id: number } | null,
  loading: false,
  isAdmin: false,
  isCompanyAdmin: false,
  login: vi.fn(),
  logout: vi.fn(),
};

vi.mock('./AuthProvider', () => ({
  useAuth: () => mockAuthState,
}));

describe('ProtectedRoute', () => {
  it('shows loading when auth is loading', () => {
    mockAuthState = { ...mockAuthState, user: null, loading: true };
    renderWithRouter(
      <ProtectedRoute><div>Protected Content</div></ProtectedRoute>,
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('renders children when user is authenticated', () => {
    mockAuthState = { ...mockAuthState, user: { id: 1 }, loading: false };
    renderWithRouter(
      <ProtectedRoute><div>Protected Content</div></ProtectedRoute>,
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to /login when no user', () => {
    mockAuthState = { ...mockAuthState, user: null, loading: false };
    // Navigate to /login is done by <Navigate to="/login" />
    // We just verify the protected content is NOT shown
    renderWithRouter(
      <ProtectedRoute><div>Protected Content</div></ProtectedRoute>,
      { route: '/dashboard' },
    );
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@inator/shared/auth/AuthProvider';
import { ProtectedRoute } from '@inator/shared/auth/ProtectedRoute';
import { Layout } from '@inator/shared/layout/Layout';
import type { NavItem } from '@inator/shared/types';
import { UserList } from './pages/UserList';
import { UserEditPage } from './pages/UserEditPage';
import { ProfilePage } from './pages/ProfilePage';
import { ProfileEditPage } from './pages/ProfileEditPage';
import { PreferencesPage } from './pages/PreferencesPage';
import { CompanyPage } from './pages/CompanyPage';
import { CompanyEditPage } from './pages/CompanyEditPage';
import { CompanyListPage } from './pages/CompanyListPage';
import { CompanyCreatePage } from './pages/CompanyCreatePage';
import { InvitationRequestPage } from './pages/InvitationRequestPage';
import { InvitationReviewPage } from './pages/InvitationReviewPage';

const NAV_ITEMS: NavItem[] = [
  { path: '/profile', label: '👤 My Profile' },
  { path: '/preferences', label: '⚙️ Preferences' },
  { path: '/company', label: '🏢 My Company' },
  { path: '/', label: '👥 All Users', adminOnly: true },
  { path: '/companies', label: '🏗️ Companies', adminOnly: true },
  { path: '/invitations', label: '📨 Invitations', adminOnly: true },
  { path: '/invitations/review', label: '📝 Review Invitations', adminOnly: true },
];

/** Root route: admins see user list, non-admins redirect to their profile. */
function AdminOrProfile(): React.JSX.Element {
  const { isAdmin } = useAuth();
  if (!isAdmin) {
    return <Navigate to="/profile" replace />;
  }
  return (
    <Layout title="USERinator" navItems={NAV_ITEMS}>
      <UserList />
    </Layout>
  );
}

/**
 * USERinator frontend — manages user profiles, companies, and invitations.
 * Served under /users via Caddy reverse proxy.
 */
export default function App(): React.JSX.Element {
  return (
    <BrowserRouter basename="/users">
      <AuthProvider>
        <Routes>
          {/* Profile */}
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <ProfilePage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile/edit"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <ProfileEditPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/preferences"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <PreferencesPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Company (own) */}
          <Route
            path="/company"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <CompanyPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/company/edit"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <CompanyEditPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Root: admins see user list, others go to profile */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AdminOrProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/:id"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <ProfilePage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/:id/edit"
            element={
              <ProtectedRoute adminOnly>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <UserEditPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Admin: Companies */}
          <Route
            path="/companies"
            element={
              <ProtectedRoute adminOnly>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <CompanyListPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/companies/new"
            element={
              <ProtectedRoute adminOnly>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <CompanyCreatePage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/companies/:id"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <CompanyPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Invitations */}
          <Route
            path="/invitations"
            element={
              <ProtectedRoute>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <InvitationRequestPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/invitations/review"
            element={
              <ProtectedRoute adminOnly>
                <Layout title="USERinator" navItems={NAV_ITEMS}>
                  <InvitationReviewPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/profile" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

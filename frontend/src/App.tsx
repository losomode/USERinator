import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './shared/auth/AuthProvider';
import { ProtectedRoute } from './shared/auth/ProtectedRoute';
import { Layout, type NavItem } from './shared/layout/Layout';
import { ProfilePage } from './modules/users/pages/ProfilePage';
import { ProfileEditPage } from './modules/users/pages/ProfileEditPage';
import { UserListPage } from './modules/users/pages/UserListPage';
import { CompanyPage } from './modules/users/pages/CompanyPage';
import { CompanyEditPage } from './modules/users/pages/CompanyEditPage';
import { InvitationRequestPage } from './modules/users/pages/InvitationRequestPage';
import { InvitationReviewPage } from './modules/users/pages/InvitationReviewPage';
import { PreferencesPage } from './modules/users/pages/PreferencesPage';

const navItems: NavItem[] = [
  { label: 'My Profile', path: '/profile' },
  { label: 'Users', path: '/users' },
  { label: 'Company', path: '/company' },
  { label: 'Invitations', path: '/invitations' },
  { label: 'Review Invitations', path: '/invitations/review', adminOnly: true },
  { label: 'Preferences', path: '/preferences' },
];

function AppRoutes() {
  return (
    <Layout title="USERinator" subtitle="User Management" navItems={navItems}>
      <Routes>
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/profile/edit" element={<ProfileEditPage />} />
        <Route path="/users" element={<UserListPage />} />
        <Route path="/company" element={<CompanyPage />} />
        <Route path="/company/edit" element={<CompanyEditPage />} />
        <Route path="/invitations" element={<InvitationRequestPage />} />
        <Route path="/invitations/review" element={<InvitationReviewPage />} />
        <Route path="/preferences" element={<PreferencesPage />} />
        <Route path="*" element={<Navigate to="/profile" replace />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div className="flex h-screen items-center justify-center"><p className="text-gray-500">Redirecting to SSO...</p></div>} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppRoutes />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

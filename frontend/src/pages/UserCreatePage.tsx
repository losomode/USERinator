import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, usersApi, companiesApi, rolesApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { Company, Role } from '../types';
import { formatRoleName } from '../types';

/** Threshold separating platform (no-company) roles from company-scoped roles. */
const PLATFORM_ROLE_THRESHOLD = 75;

/** Human-readable one-liner for platform role options. */
function describePlatformRole(name: string): string {
  if (name === 'PLATFORM_ADMIN') return 'Full read/write access across all companies';
  if (name === 'PLATFORM_MANAGER') return 'Cross-company view access, observer-level editing';
  return 'Platform role — no company required';
}

/** Human-readable one-liner for company role options. */
function describeCompanyRole(name: string): string {
  if (name === 'COMPANY_MANAGER') return 'Manage users and data within their company';
  if (name === 'COMPANY_MEMBER') return 'Read-only access to their company data';
  return 'Company-scoped role';
}

/**
 * Admin-only page for provisioning a new platform user.
 *
 * Flow:
 * 1. POST /api/auth/create-user/  — create verified AUTHinator account, get user_id + temp password
 * 2. POST /api/users/             — create matching USERinator UserProfile with role + company
 */
export function UserCreatePage(): React.JSX.Element {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState<{ username: string; tempPassword: string } | null>(null);

  const [form, setForm] = useState({
    username: '',
    email: '',
    display_name: '',
    company: '',
    role_name: '',
    role_level: 0,
  });

  useEffect(() => {
    companiesApi.list().then(setCompanies).catch(() => {});
    rolesApi.list().then(setAllRoles).catch(() => {});
  }, []);

  // Only show roles the current user is allowed to assign (≤ their own level)
  const myLevel = user?.role_level ?? 0;
  const roles = allRoles.filter((r) => r.role_level <= myLevel);

  const platformRoles = roles.filter((r) => r.role_level >= PLATFORM_ROLE_THRESHOLD);
  const companyRoles = roles.filter((r) => r.role_level < PLATFORM_ROLE_THRESHOLD);

  // Is the currently selected role a platform (no-company) role?
  const selectedRole = roles.find((r) => r.role_name === form.role_name);
  const isPlatformRole = (selectedRole?.role_level ?? form.role_level) >= PLATFORM_ROLE_THRESHOLD;

  const handleRoleChange = (roleName: string): void => {
    const role = roles.find((r) => r.role_name === roleName);
    setForm((prev) => ({
      ...prev,
      role_name: roleName,
      role_level: role?.role_level ?? 10,
      // Clear company when switching to a platform role
      company: role && role.role_level >= PLATFORM_ROLE_THRESHOLD ? '' : prev.company,
    }));
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!form.role_name) {
      setError('Please select a role.');
      return;
    }
    if (!isPlatformRole && !form.company) {
      setError('Company is required for company-level roles.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      // Step 1: Create AUTHinator user.
      // PLATFORM_ADMIN (level 100) users must have role='ADMIN' in AUTHinator so they
      // can call admin-gated endpoints (e.g. create_user) from their own session.
      const authUser = await authApi.createUser({
        username: form.username,
        email: form.email,
        role: form.role_level >= 100 ? 'ADMIN' : 'USER',
      });

      // Step 2: Create USERinator profile (no company for platform roles)
      await usersApi.create({
        user_id: authUser.id,
        username: authUser.username,
        email: authUser.email,
        company: isPlatformRole ? (undefined as unknown as number) : Number(form.company),
        display_name: form.display_name || authUser.username,
        role_name: form.role_name,
        role_level: form.role_level,
      });

      setCreated({ username: authUser.username, tempPassword: authUser.temp_password });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string; username?: string[]; email?: string[] } } })
          ?.response?.data?.detail ??
        (err as { response?: { data?: { username?: string[] } } })?.response?.data?.username?.[0] ??
        (err as { response?: { data?: { email?: string[] } } })?.response?.data?.email?.[0] ??
        'Failed to create user.';
      setError(String(msg));
    } finally {
      setSaving(false);
    }
  };

  if (created) {
    return (
      <div className="max-w-lg">
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-6">
          <h2 className="mb-2 text-xl font-semibold text-green-800">User Created Successfully</h2>
          <p className="mb-1 text-sm text-green-700">
            <strong>Username:</strong> {created.username}
          </p>
          <p className="mb-4 text-sm text-green-700">
            <strong>Temporary Password:</strong>{' '}
            <code className="rounded bg-green-100 px-1 font-mono">{created.tempPassword}</code>
          </p>
          <p className="text-xs text-green-600">
            Share these credentials with the user. They should change their password after first login.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/')}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            Back to Users
          </button>
          <button
            onClick={() => {
              setCreated(null);
              setForm({ username: '', email: '', display_name: '', company: '', role_name: '', role_level: 0 });
            }}
            className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
          >
            Create Another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      <h2 className="mb-4 text-2xl font-bold">Create User</h2>
      <p className="mb-4 text-sm text-gray-500">
        Creates an account in both AUTHinator and USERinator. A temporary password will be generated and displayed for you to share.
      </p>
      {error && <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Username <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            required
            minLength={3}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Email <span className="text-red-500">*</span>
          </label>
          <input
            type="email"
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Display Name</label>
          <input
            type="text"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            placeholder="Defaults to username if blank"
            value={form.display_name}
            onChange={(e) => setForm({ ...form, display_name: e.target.value })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Role</label>
          <select
            required
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={form.role_name}
            onChange={(e) => handleRoleChange(e.target.value)}
          >
            <option value="" disabled>Please select a role…</option>
            {platformRoles.length > 0 && (
              <optgroup label="— Platform Roles (no company) —">
                {platformRoles.map((r) => (
                  <option key={r.id} value={r.role_name}>
                    {formatRoleName(r.role_name)} — {describePlatformRole(r.role_name)}
                  </option>
                ))}
              </optgroup>
            )}
            {companyRoles.length > 0 && (
              <optgroup label="— Company Roles —">
                {companyRoles.map((r) => (
                  <option key={r.id} value={r.role_name}>
                    {formatRoleName(r.role_name)} — {describeCompanyRole(r.role_name)}
                  </option>
                ))}
              </optgroup>
            )}
            {roles.length === 0 && (
              <option value="MEMBER">MEMBER (level 10)</option>
            )}
          </select>
          {isPlatformRole && (
            <p className="mt-1 text-xs text-blue-600">
              Platform Admins are not tied to any company — this user will have cross-company access.
            </p>
          )}
        </div>

        {/* Company field — hidden for platform roles */}
        {!isPlatformRole && (
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Company <span className="text-red-500">*</span>
            </label>
            <select
              required={!isPlatformRole}
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
            >
              <option value="">Select a company</option>
              {companies.map((c) => (
                <option key={c.id} value={String(c.id)}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Creating…' : 'Create User'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

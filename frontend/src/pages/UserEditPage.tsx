import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usersApi, companiesApi, rolesApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { UserProfile, Company, Role } from '../types';
import { formatRoleName } from '../types';

const PLATFORM_ROLE_THRESHOLD = 60;

/** Admin fields that go beyond self-edit. */
interface AdminEditForm {
  display_name: string;
  phone: string;
  bio: string;
  job_title: string;
  department: string;
  location: string;
  company: number | null;  // null = no company (platform user)
  role_name: string;
  role_level: number;
  is_active: boolean;
}

export function UserEditPage(): React.JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [form, setForm] = useState<AdminEditForm | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [credForm, setCredForm] = useState({ new_username: '', password: '' });
  const [credSaving, setCredSaving] = useState(false);
  const [credMsg, setCredMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    companiesApi.list().then(setCompanies).catch(() => {/* best-effort */});
    rolesApi.list().then(setAllRoles).catch(() => {/* best-effort */});
  }, []);

  const myLevel = currentUser?.role_level ?? 0;
  // Roles the current admin can assign (≤ their own level)
  const assignableRoles = allRoles.filter((r) => r.role_level <= myLevel);

  useEffect(() => {
    if (!id) return;
    usersApi
      .get(Number(id))
      .then((p) => {
        setProfile(p);
        // Guard against null: typeof null === 'object' in JS
        const companyId =
          p.company != null && typeof p.company === 'object'
            ? p.company.id
            : (p.company ?? null);
        setForm({
          display_name: p.display_name,
          phone: p.phone,
          bio: p.bio,
          job_title: p.job_title,
          department: p.department,
          location: p.location,
          company: companyId,
          role_name: p.role_name,
          role_level: p.role_level,
          is_active: p.is_active,
        });
      })
      .catch(() => setError('Failed to load user.'));
  }, [id]);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!id || !form) return;
    setSaving(true);
    setError('');
    try {
      await usersApi.update(Number(id), form);
      navigate(`/${id}`);
    } catch {
      setError('Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };


  if (error && !profile) return <div className="text-red-600">{error}</div>;
  if (!profile || !form) return <div>Loading user...</div>;

  const textFields: { label: string; key: keyof AdminEditForm }[] = [
    { label: 'Display Name', key: 'display_name' },
    { label: 'Job Title', key: 'job_title' },
    { label: 'Department', key: 'department' },
    { label: 'Location', key: 'location' },
    { label: 'Phone', key: 'phone' },
  ];

  return (
    <div className="max-w-lg">
      <h2 className="mb-1 text-2xl font-bold">Edit User</h2>
      <p className="mb-4 text-sm text-gray-500">
        {profile.display_name} (@{profile.username})
      </p>
      {error && <p className="mb-2 text-red-600">{error}</p>}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        {textFields.map(({ label, key }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700">{label}</label>
            <input
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={String(form[key] ?? '')}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          </div>
        ))}

        <div>
          <label className="block text-sm font-medium text-gray-700">Bio</label>
          <textarea
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            rows={3}
            value={form.bio}
            onChange={(e) => setForm({ ...form, bio: e.target.value })}
          />
        </div>

        <hr className="my-2" />
        <h3 className="text-sm font-semibold text-gray-800">Admin Fields</h3>

        <div>
          <label className="block text-sm font-medium text-gray-700">Company</label>
          <select
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={form.company ?? ''}
            onChange={(e) =>
              setForm({ ...form, company: e.target.value ? Number(e.target.value) : null })
            }
          >
            <option value="">— No Company (Platform User) —</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Role</label>
          <select
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={form.role_name}
            onChange={(e) => {
              const name = e.target.value;
              const matched = assignableRoles.find((r) => r.role_name === name);
              const level = matched?.role_level ?? form.role_level;
              const isPlatform = level >= PLATFORM_ROLE_THRESHOLD;
              setForm({ ...form, role_name: name, role_level: level, company: isPlatform ? 0 : form.company });
            }}
          >
            {assignableRoles.filter((r) => r.role_level >= PLATFORM_ROLE_THRESHOLD).length > 0 && (
              <optgroup label="— Platform Roles (no company) —">
                {assignableRoles
                  .filter((r) => r.role_level >= PLATFORM_ROLE_THRESHOLD)
                  .map((r) => <option key={r.id} value={r.role_name}>{formatRoleName(r.role_name)}</option>)}
              </optgroup>
            )}
            {assignableRoles.filter((r) => r.role_level < PLATFORM_ROLE_THRESHOLD).length > 0 && (
              <optgroup label="— Company Roles —">
                {assignableRoles
                  .filter((r) => r.role_level < PLATFORM_ROLE_THRESHOLD)
                  .map((r) => <option key={r.id} value={r.role_name}>{formatRoleName(r.role_name)}</option>)}
              </optgroup>
            )}
            {assignableRoles.length === 0 && (
              <option value={form.role_name}>{formatRoleName(form.role_name)}</option>
            )}
          </select>
          <p className="mt-1 text-xs text-gray-400">Role level: {form.role_level}</p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_active"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
            className="h-4 w-4 rounded border-gray-300"
          />
          <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
            Active
          </label>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/${id}`)}
            className="rounded border px-4 py-2 text-sm"
          >
            Cancel
          </button>
        </div>
      </form>

      {/* Change username / password for lower-level users */}
      <div className="mt-8 border-t pt-6">
        <h3 className="mb-1 text-sm font-semibold text-gray-800">Change Username / Password</h3>
        <p className="mb-3 text-xs text-gray-400">Fill in one or both fields. Changes take effect immediately.</p>
        {credMsg && (
          <p className={`mb-3 text-sm ${credMsg.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>
            {credMsg.text}
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!profile) return;
            if (!credForm.new_username && !credForm.password) {
              setCredMsg({ type: 'error', text: 'Enter a new username, a new password, or both.' });
              return;
            }
            setCredSaving(true);
            setCredMsg(null);
            const payload: { password?: string; new_username?: string } = {};
            if (credForm.password) payload.password = credForm.password;
            if (credForm.new_username) payload.new_username = credForm.new_username;
            usersApi.setCredentials(profile.user_id, payload)
              .then((res) => {
                setCredMsg({ type: 'success', text: res.detail });
                setCredForm({ new_username: '', password: '' });
                // Refresh profile to show updated username
                if (credForm.new_username) {
                  setProfile((prev) => prev ? { ...prev, username: credForm.new_username } : prev);
                }
              })
              .catch((err: unknown) => {
                const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to update credentials.';
                setCredMsg({ type: 'error', text: detail });
              })
              .finally(() => setCredSaving(false));
          }}
          className="space-y-3"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700">New Username</label>
            <input
              type="text"
              minLength={3}
              placeholder="Leave blank to keep current"
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={credForm.new_username}
              onChange={(e) => setCredForm({ ...credForm, new_username: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">New Password</label>
            <input
              type="password"
              minLength={8}
              placeholder="Leave blank to keep current (min 8 chars)"
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={credForm.password}
              onChange={(e) => setCredForm({ ...credForm, password: e.target.value })}
            />
          </div>
          <button
            type="submit"
            disabled={credSaving}
            className="rounded bg-orange-600 px-4 py-2 text-sm text-white hover:bg-orange-700 disabled:opacity-50"
          >
            {credSaving ? 'Updating…' : 'Update Credentials'}
          </button>
        </form>
      </div>
    </div>
  );
}

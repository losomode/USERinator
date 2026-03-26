import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { usersApi, authApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { UserProfile } from '../types';
import { formatRoleName } from '../types';

/** Inline modal for changing own password. */
function ChangePasswordModal({ onClose }: { onClose: () => void }): React.JSX.Element {
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm: '' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (form.new_password !== form.confirm) {
      setMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    setSaving(true);
    setMsg(null);
    try {
      await authApi.changePassword({ current_password: form.current_password, new_password: form.new_password });
      setMsg({ type: 'success', text: 'Password updated. You may need to log in again.' });
    } catch {
      setMsg({ type: 'error', text: 'Failed to change password. Check your current password.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold">Change Password</h3>
        {msg && (
          <p className={`mb-3 text-sm ${msg.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>{msg.text}</p>
        )}
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
          {(['current_password', 'new_password', 'confirm'] as const).map((key) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700">
                {key === 'current_password' ? 'Current Password' : key === 'new_password' ? 'New Password' : 'Confirm New Password'}
              </label>
              <input
                type="password"
                required
                className="mt-1 w-full rounded border px-3 py-2 text-sm"
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving…' : 'Update Password'}
            </button>
            <button type="button" onClick={onClose} className="rounded border px-4 py-2 text-sm hover:bg-gray-50">
              Close
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/** Inline modal for changing own username. */
function ChangeUsernameModal({ onClose }: { onClose: () => void }): React.JSX.Element {
  const [form, setForm] = useState({ new_username: '', password: '' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    try {
      const res = await authApi.changeUsername(form);
      setMsg({ type: 'success', text: `Username changed to "${res.username}". Log out and back in for full effect.` });
    } catch {
      setMsg({ type: 'error', text: 'Failed to change username. Check your password and try again.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 text-lg font-semibold">Change Username</h3>
        {msg && (
          <p className={`mb-3 text-sm ${msg.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>{msg.text}</p>
        )}
        <form onSubmit={(e) => void handleSubmit(e)} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">New Username</label>
            <input
              type="text"
              required
              minLength={3}
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={form.new_username}
              onChange={(e) => setForm({ ...form, new_username: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Current Password (to confirm)</label>
            <input
              type="password"
              required
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>
          <div className="flex gap-2 pt-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? 'Saving…' : 'Update Username'}
            </button>
            <button type="button" onClick={onClose} className="rounded border px-4 py-2 text-sm hover:bg-gray-50">
              Close
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ProfilePage(): React.JSX.Element {
  const { id } = useParams<{ id: string }>();
  const { user, isAdmin } = useAuth();
  // Managers (30+) can edit users in their company, not just admins
  const canEdit = (user?.role_level ?? 0) >= 30;
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState('');
  const [showChangePw, setShowChangePw] = useState(false);
  const [showChangeUn, setShowChangeUn] = useState(false);

  // Determine if viewing own profile
  const isOwnProfile = !id || (profile && profile.user_id === user?.id);

  useEffect(() => {
    const fetchProfile = id ? usersApi.get(Number(id)) : usersApi.me();
    fetchProfile.then(setProfile).catch(() => setError('Failed to load profile.'));
  }, [id]);

  if (error) return <div className="text-red-600">{error}</div>;
  if (!profile) return <div>Loading profile...</div>;

  return (
    <div className="max-w-2xl">
      {showChangePw && <ChangePasswordModal onClose={() => setShowChangePw(false)} />}
      {showChangeUn && <ChangeUsernameModal onClose={() => setShowChangeUn(false)} />}

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold">{profile.display_name}</h2>
        <div className="flex flex-wrap gap-2">
          {isOwnProfile && (
            <>
              <Link to="/profile/edit" className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
                Edit Profile
              </Link>
              <button
                onClick={() => setShowChangePw(true)}
                className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
              >
                Change Password
              </button>
              <button
                onClick={() => setShowChangeUn(true)}
                className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
              >
                Change Username
              </button>
            </>
          )}
          {!isOwnProfile && canEdit && (
            <Link to={`/${String(profile.user_id)}/edit`} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
              Edit User
            </Link>
          )}
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="font-medium text-gray-500">Username</dt>
        <dd>{profile.username}</dd>
        <dt className="font-medium text-gray-500">Email</dt>
        <dd>{profile.email}</dd>
        {/* Company: show as a link for platform users who can navigate to it */}
        {profile.company != null && (
          <>
            <dt className="font-medium text-gray-500">Company</dt>
            <dd>
              {isAdmin
                ? (
                  <Link
                    to={`/companies/${String(typeof profile.company === 'object' ? profile.company.id : profile.company)}`}
                    className="text-blue-600 hover:underline"
                  >
                    {profile.company_name ?? (typeof profile.company === 'object' ? profile.company.name : `#${String(profile.company)}`)}
                  </Link>
                )
                : (profile.company_name ?? '—')}
            </dd>
          </>
        )}
        <dt className="font-medium text-gray-500">Job Title</dt>
        <dd>{profile.job_title || '—'}</dd>
        <dt className="font-medium text-gray-500">Department</dt>
        <dd>{profile.department || '—'}</dd>
        <dt className="font-medium text-gray-500">Location</dt>
        <dd>{profile.location || '—'}</dd>
        <dt className="font-medium text-gray-500">Phone</dt>
        <dd>{profile.phone || '—'}</dd>
        <dt className="font-medium text-gray-500">Role</dt>
        <dd>{formatRoleName(profile.role_name)} (level {profile.role_level})</dd>
        <dt className="font-medium text-gray-500">Bio</dt>
        <dd className="col-span-2">{profile.bio || '—'}</dd>
      </dl>
    </div>
  );
}

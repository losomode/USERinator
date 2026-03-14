import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { usersApi, companiesApi } from '../api';
import type { UserProfile, Company } from '../types';

/** Admin fields that go beyond self-edit. */
interface AdminEditForm {
  display_name: string;
  phone: string;
  bio: string;
  job_title: string;
  department: string;
  location: string;
  company: number;
  role_name: string;
  role_level: number;
  is_active: boolean;
}

export function UserEditPage(): React.JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [form, setForm] = useState<AdminEditForm | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    companiesApi.list().then(setCompanies).catch(() => {/* best-effort */});
  }, []);

  useEffect(() => {
    if (!id) return;
    usersApi
      .get(Number(id))
      .then((p) => {
        setProfile(p);
        const companyId = typeof p.company === 'object' ? p.company.id : p.company;
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
            value={form.company}
            onChange={(e) => setForm({ ...form, company: Number(e.target.value) })}
          >
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Role Name</label>
          <select
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            value={form.role_name}
            onChange={(e) => {
              const name = e.target.value;
              const level = name === 'ADMIN' ? 100 : name === 'MANAGER' ? 30 : 10;
              setForm({ ...form, role_name: name, role_level: level });
            }}
          >
            <option value="MEMBER">MEMBER</option>
            <option value="MANAGER">MANAGER</option>
            <option value="ADMIN">ADMIN</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Role Level</label>
          <input
            type="number"
            className="mt-1 w-full rounded border bg-gray-50 px-3 py-2 text-sm"
            value={form.role_level}
            readOnly
          />
          <p className="mt-1 text-xs text-gray-400">Auto-set from role name</p>
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
    </div>
  );
}

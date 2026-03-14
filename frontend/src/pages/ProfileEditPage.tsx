import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usersApi } from '../api';
import type { UserProfile, UpdateProfileInput } from '../types';

export function ProfileEditPage(): React.JSX.Element {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [form, setForm] = useState<UpdateProfileInput>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    usersApi.me().then((p) => {
      setProfile(p);
      setForm({
        display_name: p.display_name,
        phone: p.phone,
        bio: p.bio,
        job_title: p.job_title,
        department: p.department,
        location: p.location,
      });
    });
  }, []);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await usersApi.updateMe(form);
      navigate('/profile');
    } catch {
      setError('Failed to save profile.');
    } finally {
      setSaving(false);
    }
  };

  if (!profile) return <div>Loading...</div>;

  const fields: { label: string; key: keyof UpdateProfileInput; type?: string }[] = [
    { label: 'Display Name', key: 'display_name' },
    { label: 'Job Title', key: 'job_title' },
    { label: 'Department', key: 'department' },
    { label: 'Location', key: 'location' },
    { label: 'Phone', key: 'phone' },
  ];

  return (
    <div className="max-w-lg">
      <h2 className="mb-4 text-2xl font-bold">Edit Profile</h2>
      {error && <p className="mb-2 text-red-600">{error}</p>}
      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        {fields.map(({ label, key }) => (
          <div key={key}>
            <label className="block text-sm font-medium text-gray-700">{label}</label>
            <input
              className="mt-1 w-full rounded border px-3 py-2 text-sm"
              value={(form[key] as string) ?? ''}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            />
          </div>
        ))}
        <div>
          <label className="block text-sm font-medium text-gray-700">Bio</label>
          <textarea
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
            rows={3}
            value={form.bio ?? ''}
            onChange={(e) => setForm({ ...form, bio: e.target.value })}
          />
        </div>
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button type="button" onClick={() => navigate('/profile')} className="rounded border px-4 py-2 text-sm">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

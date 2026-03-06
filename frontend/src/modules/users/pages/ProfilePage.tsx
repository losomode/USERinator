import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { userApi } from '../api';
import type { UserProfile } from '../types';

export function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    userApi.getMe().then(setProfile).catch(() => setError('Failed to load profile.'));
  }, []);

  if (error) return <div className="text-red-600">{error}</div>;
  if (!profile) return <div>Loading profile...</div>;

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold">{profile.display_name}</h2>
        <Link to="/profile/edit" className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
          Edit Profile
        </Link>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="font-medium text-gray-500">Username</dt>
        <dd>{profile.username}</dd>
        <dt className="font-medium text-gray-500">Email</dt>
        <dd>{profile.email}</dd>
        <dt className="font-medium text-gray-500">Job Title</dt>
        <dd>{profile.job_title || '—'}</dd>
        <dt className="font-medium text-gray-500">Department</dt>
        <dd>{profile.department || '—'}</dd>
        <dt className="font-medium text-gray-500">Location</dt>
        <dd>{profile.location || '—'}</dd>
        <dt className="font-medium text-gray-500">Phone</dt>
        <dd>{profile.phone || '—'}</dd>
        <dt className="font-medium text-gray-500">Role</dt>
        <dd>{profile.role_name} (level {profile.role_level})</dd>
        <dt className="font-medium text-gray-500">Bio</dt>
        <dd className="col-span-2">{profile.bio || '—'}</dd>
      </dl>
    </div>
  );
}

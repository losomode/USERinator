import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { usersApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { UserProfile } from '../types';

export function ProfilePage(): React.JSX.Element {
  const { id } = useParams<{ id: string }>();
  const { user, isAdmin } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState('');
  
  // Determine if viewing own profile
  const isOwnProfile = !id || (profile && profile.user_id === user?.id);

  useEffect(() => {
    // If id parameter exists, fetch that user's profile
    // Otherwise fetch current user's profile
    const fetchProfile = id
      ? usersApi.get(Number(id))
      : usersApi.me();
    
    fetchProfile
      .then(setProfile)
      .catch(() => setError('Failed to load profile.'));
  }, [id]);

  if (error) return <div className="text-red-600">{error}</div>;
  if (!profile) return <div>Loading profile...</div>;

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold">{profile.display_name}</h2>
        <div className="flex gap-2">
          {isOwnProfile && (
            <Link to="/profile/edit" className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
              Edit Profile
            </Link>
          )}
          {!isOwnProfile && isAdmin && (
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

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { usersApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { UserProfile } from '../types';

/** Badge color based on role level. */
function roleBadgeClass(level: number): string {
  if (level >= 100) return 'bg-purple-100 text-purple-800';
  if (level >= 30) return 'bg-blue-100 text-blue-800';
  return 'bg-gray-100 text-gray-800';
}

export function UserList(): React.JSX.Element {
  const { isAdmin } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const params: Record<string, string> = {};
    if (search) params.search = search;

    usersApi
      .list(params)
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [search]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <input
          type="text"
          placeholder="Search users…"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : users.length === 0 ? (
        <p className="text-gray-500">No users found.</p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Email
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Role
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                  Company
                </th>
                {isAdmin && (
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {users.map((u) => (
                <tr key={u.user_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/${String(u.user_id)}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {u.display_name}
                    </Link>
                    <span className="ml-2 text-sm text-gray-400">@{u.username}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${roleBadgeClass(u.role_level)}`}
                    >
                      {u.role_name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{typeof u.company === 'object' ? u.company?.name : '—'}</td>
                  {isAdmin && (
                    <td className="px-4 py-3">
                      <Link
                        to={`/${String(u.user_id)}/edit`}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        Edit
                      </Link>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

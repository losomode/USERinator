import { useEffect, useState } from 'react';
import { userApi } from '../api';
import type { UserProfile } from '../types';

export function UserListPage() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params: Record<string, unknown> = {};
    if (search) params.search = search;
    userApi.list(params).then((r) => { setUsers(r.results); setLoading(false); });
  }, [search]);

  return (
    <div>
      <h2 className="mb-4 text-2xl font-bold">Users</h2>
      <input
        className="mb-4 w-64 rounded border px-3 py-2 text-sm"
        placeholder="Search users..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {loading ? (
        <div>Loading...</div>
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="border-b text-gray-500">
            <tr>
              <th className="py-2">Name</th>
              <th>Email</th>
              <th>Job Title</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.user_id} className="border-b">
                <td className="py-2 font-medium">{u.display_name}</td>
                <td>{u.email}</td>
                <td>{u.job_title || '—'}</td>
                <td>{u.role_name}</td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={4} className="py-4 text-center text-gray-400">No users found.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

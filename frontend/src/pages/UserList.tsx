import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usersApi, companiesApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { UserProfile, Company } from '../types';
import { formatRoleName } from '../types';

/** Badge color based on role level. */
function roleBadgeClass(level: number): string {
  if (level >= 100) return 'bg-purple-100 text-purple-800';
  if (level >= 30) return 'bg-blue-100 text-blue-800';
  return 'bg-gray-100 text-gray-800';
}

export function UserList(): React.JSX.Element {
  const { isAdmin, user } = useAuth();
  // Company managers (30+) can edit users in their company; members (10) cannot.
  const canEdit = (user?.role_level ?? 0) >= 30;
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyFilter, setCompanyFilter] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Load company list for the filter dropdown (admin only)
  useEffect(() => {
    if (isAdmin) {
      companiesApi.list().then(setCompanies).catch(() => {/* best-effort */});
    }
  }, [isAdmin]);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (search) params.search = search;
    if (companyFilter) params.company = companyFilter;

    usersApi
      .list(params)
      .then(setUsers)
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
  }, [search, companyFilter]);

  const handleDelete = async (userId: number, displayName: string): Promise<void> => {
    if (!window.confirm(
      `Remove "${displayName}"?\n\n` +
      `• Their login account will be deactivated immediately.\n` +
      `• They will be removed from all user lists.\n` +
      `• Their historical data (RMAs, orders, etc.) is preserved for audit purposes.\n\n` +
      `This action can be reversed by re-creating the user.`
    )) return;
    setDeletingId(userId);
    try {
      await usersApi.delete(userId);
      setUsers((prev) => prev.filter((u) => u.user_id !== userId));
    } catch {
      alert('Failed to deactivate user.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <div className="ml-auto flex flex-wrap gap-2">
          <input
            type="text"
            placeholder="Search users…"
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {isAdmin && companies.length > 0 && (
            <select
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={companyFilter}
              onChange={(e) => setCompanyFilter(e.target.value)}
            >
              <option value="">All Companies</option>
              {companies.map((c) => (
                <option key={c.id} value={String(c.id)}>{c.name}</option>
              ))}
            </select>
          )}
          {isAdmin && (
            <button
              onClick={() => navigate('/users/new')}
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              + Create User
            </button>
          )}
        </div>
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
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Email</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Role</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Company</th>
                {canEdit && (
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {users.map((u) => (
                <tr key={u.user_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link to={`/${String(u.user_id)}`} className="font-medium text-blue-600 hover:underline">
                      {u.display_name}
                    </Link>
                    <span className="ml-2 text-sm text-gray-400">@{u.username}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${roleBadgeClass(u.role_level)}`}>
                      {formatRoleName(u.role_name)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {u.company_name ?? '—'}
                  </td>
                  {canEdit && (
                    <td className="px-4 py-3">
                      <div className="flex gap-3">
                        <Link to={`/${String(u.user_id)}/edit`} className="text-sm text-blue-600 hover:underline">
                          Edit
                        </Link>
                        {isAdmin && (
                          <button
                            onClick={() => void handleDelete(u.user_id, u.display_name)}
                            disabled={deletingId === u.user_id}
                            className="text-sm text-red-600 hover:underline disabled:opacity-50"
                          >
                            {deletingId === u.user_id ? 'Removing…' : 'Remove'}
                          </button>
                        )}
                      </div>
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

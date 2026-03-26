import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { usersApi, companiesApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { UserProfile, Company } from '../types';
import { formatRoleName } from '../types';

/** Badge color based on role level. */
function roleBadgeClass(level: number): string {
  if (level >= 100) return 'bg-purple-100 text-purple-800';
  if (level >= 50) return 'bg-indigo-100 text-indigo-800';
  if (level >= 30) return 'bg-blue-100 text-blue-800';
  return 'bg-gray-100 text-gray-800';
}

/** Status badge for active/deactivated/marked-for-deletion. */
function StatusBadge({ u }: { u: UserProfile }): React.JSX.Element {
  if (u.marked_for_deletion) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-800">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Pending Deletion
      </span>
    );
  }
  if (!u.is_active) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-semibold text-orange-800">
        <span className="h-1.5 w-1.5 rounded-full bg-orange-500" />
        Deactivated
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-800">
      <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
      Active
    </span>
  );
}

export function UserList(): React.JSX.Element {
  const { isAdmin, user } = useAuth();
  const navigate = useNavigate();
  const myLevel = user?.role_level ?? 0;
  const myCompany = (user as { company_id?: number } | null)?.company_id;

  // Permission helpers
  const canEdit = myLevel >= 30;        // show Edit button
  const isPlatformAdmin = isAdmin;      // level 100, can permanently delete

  /** Can this acting user deactivate the target user? */
  function canDeactivate(target: UserProfile): boolean {
    if (!target.is_active) return false; // already deactivated
    if (myLevel < 30) return false;      // members can't deactivate
    if (myLevel >= 100) return true;     // platform admins can deactivate anyone (use Remove instead)
    return target.role_level < myLevel;  // can only deactivate lower-level users
  }

  /** Can this acting user mark a deactivated user for deletion? */
  function canMarkForDeletion(target: UserProfile): boolean {
    if (target.is_active || target.marked_for_deletion) return false;
    if (myLevel < 30) return false;
    if (myLevel >= 100) return true;
    return target.role_level < myLevel;
  }

  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyFilter, setCompanyFilter] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [actionMsg, setActionMsg] = useState<{ id: number; text: string; ok: boolean } | null>(null);
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

  const withActionId = (userId: number, fn: () => Promise<void>): (() => Promise<void>) => async () => {
    setDeletingId(userId);
    setActionMsg(null);
    try {
      await fn();
    } finally {
      setDeletingId(null);
    }
  };

  const handleDeactivate = (u: UserProfile) => withActionId(u.user_id, async () => {
    if (!window.confirm(`Deactivate "${u.display_name}"?\n\nThey will no longer be able to log in. You can mark them for deletion afterwards.`)) return;
    try {
      await usersApi.deactivate(u.user_id);
      setUsers((prev) => prev.map((x) => x.user_id === u.user_id ? { ...x, is_active: false } : x));
      setActionMsg({ id: u.user_id, text: `${u.display_name} has been deactivated.`, ok: true });
    } catch {
      setActionMsg({ id: u.user_id, text: 'Failed to deactivate user.', ok: false });
    }
  });

  const handleMarkForDeletion = (u: UserProfile) => withActionId(u.user_id, async () => {
    if (!window.confirm(`Mark "${u.display_name}" for deletion?\n\nA platform admin will review and permanently delete their account.`)) return;
    try {
      await usersApi.markForDeletion(u.user_id);
      setUsers((prev) => prev.map((x) => x.user_id === u.user_id ? { ...x, marked_for_deletion: true } : x));
      setActionMsg({ id: u.user_id, text: `${u.display_name} has been marked for deletion.`, ok: true });
    } catch {
      setActionMsg({ id: u.user_id, text: 'Failed to mark user for deletion.', ok: false });
    }
  });

  // Platform admin: permanently remove (full wipe from both systems)
  const handlePermanentDelete = (u: UserProfile) => withActionId(u.user_id, async () => {
    if (!window.confirm(
      `Permanently delete "${u.display_name}"?\n\n` +
      `• This is irreversible.\n` +
      `• Their AUTHinator account will be fully removed.\n` +
      `• Historical data (RMAs, orders) is preserved.`
    )) return;
    try {
      await usersApi.delete(u.user_id);
      setUsers((prev) => prev.filter((x) => x.user_id !== u.user_id));
    } catch {
      setActionMsg({ id: u.user_id, text: 'Failed to permanently delete user.', ok: false });
    }
  });

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
                <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                {canEdit && (
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {users.filter((u) => !u.marked_for_deletion).map((u) => (
                <tr key={u.user_id} className={`hover:bg-gray-50 ${!u.is_active ? 'opacity-60' : ''}`}>
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
                  <td className="px-4 py-3 text-sm text-gray-600">{u.company_name ?? '—'}</td>
                  <td className="px-4 py-3"><StatusBadge u={u} /></td>
                  {canEdit && (
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        {u.is_active && (
                          <Link to={`/${String(u.user_id)}/edit`} className="text-sm text-blue-600 hover:underline">
                            Edit
                          </Link>
                        )}
                        {canDeactivate(u) && (
                          <button
                            onClick={() => void handleDeactivate(u)()}
                            disabled={deletingId === u.user_id}
                            className="text-sm text-orange-600 hover:underline disabled:opacity-50"
                          >
                            {deletingId === u.user_id ? 'Working…' : 'Deactivate'}
                          </button>
                        )}
                        {canMarkForDeletion(u) && (
                          <button
                            onClick={() => void handleMarkForDeletion(u)()}
                            disabled={deletingId === u.user_id}
                            className="text-sm text-red-600 hover:underline disabled:opacity-50"
                          >
                            Mark for Deletion
                          </button>
                        )}
                        {actionMsg?.id === u.user_id && (
                          <span className={`text-xs ${actionMsg.ok ? 'text-green-700' : 'text-red-600'}`}>
                            {actionMsg.text}
                          </span>
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

      {/* Platform admin: review users marked for permanent deletion */}
      {isPlatformAdmin && users.some((u) => u.marked_for_deletion) && (
        <div className="mt-10">
          <h2 className="mb-3 text-lg font-semibold text-red-800">Users Marked for Deletion</h2>
          <p className="mb-4 text-sm text-gray-500">
            These users have been flagged by a company manager or admin. Review and permanently delete or clear the flag.
          </p>
          <div className="overflow-hidden rounded-lg border border-red-200">
            <table className="min-w-full divide-y divide-red-200">
              <thead className="bg-red-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-red-600">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-red-600">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-red-600">Company</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-red-600">Flagged</th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-red-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-red-100 bg-white">
                {users.filter((u) => u.marked_for_deletion).map((u) => (
                  <tr key={u.user_id} className="hover:bg-red-50">
                    <td className="px-4 py-3">
                      <span className="font-medium text-gray-800">{u.display_name}</span>
                      <span className="ml-2 text-xs text-gray-400">@{u.username}</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.company_name ?? '—'}</td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {u.marked_for_deletion_at
                        ? new Date(u.marked_for_deletion_at).toLocaleDateString()
                        : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => void handlePermanentDelete(u)()}
                        disabled={deletingId === u.user_id}
                        className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        {deletingId === u.user_id ? 'Deleting…' : 'Permanently Delete'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

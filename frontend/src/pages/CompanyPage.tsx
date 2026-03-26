import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { companiesApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { Company, UserProfile } from '../types';
import { formatRoleName } from '../types';

export function CompanyPage(): React.JSX.Element {
  const { id } = useParams<{ id: string }>();
  const { user, isAdmin } = useAuth();
  const isCompanyAdmin = user?.role_level != null && user.role_level >= 30;
  const [company, setCompany] = useState<Company | null>(null);
  const [companyUsers, setCompanyUsers] = useState<UserProfile[]>([]);
  const [noCompany, setNoCompany] = useState(false);
  const [error, setError] = useState('');

  // Edit link: admin viewing /companies/:id should edit via /companies/:id/edit;
  // managers viewing /company should edit via /company/edit
  const editLink = id ? `/companies/${id}/edit` : '/company/edit';

  useEffect(() => {
    setNoCompany(false);
    setError('');
    const fetchCompany = id ? companiesApi.get(Number(id)) : companiesApi.getMy();
    fetchCompany
      .then((c) => {
        setCompany(c);
        // Load company users
        companiesApi.getUsers(c.id).then(setCompanyUsers).catch(() => {/* best-effort */});
      })
      .catch((err) => {
        // 404 at /company means this user has no associated company
        if (!id && err?.response?.status === 404) {
          setNoCompany(true);
        } else {
          setError('Failed to load company.');
        }
      });
  }, [id]);

  if (noCompany) {
    return (
      <div className="rounded border border-gray-200 bg-gray-50 p-6">
        <h2 className="mb-2 text-xl font-semibold text-gray-700">No Company Associated</h2>
        <p className="text-sm text-gray-500">
          {isAdmin
            ? 'As a platform admin you are not tied to a specific company. Browse and manage all companies from the '
            : 'You are not currently associated with a company. Contact an administrator.'}
          {isAdmin && (
            <Link to="/companies" className="text-blue-600 underline">
              Companies tab
            </Link>
          )}
          .
        </p>
      </div>
    );
  }

  if (error) return <div className="text-red-600">{error}</div>;
  if (!company) return <div>Loading company...</div>;

  return (
    <div className="max-w-3xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold">{company.name}</h2>
        {isCompanyAdmin && (
          <Link to={editLink} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            Edit Company
          </Link>
        )}
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="font-medium text-gray-500">Address</dt>
        <dd>{company.address || '—'}</dd>
        <dt className="font-medium text-gray-500">Industry</dt>
        <dd>{company.industry || '—'}</dd>
        <dt className="font-medium text-gray-500">Size</dt>
        <dd>{company.company_size || '—'}</dd>
        <dt className="font-medium text-gray-500">Website</dt>
        <dd>{company.website ? <a href={company.website} className="text-blue-600">{company.website}</a> : '—'}</dd>
        <dt className="font-medium text-gray-500">Phone</dt>
        <dd>{company.phone || '—'}</dd>
        <dt className="font-medium text-gray-500">Billing Contact</dt>
        <dd>{company.billing_contact_email || '—'}</dd>
        <dt className="font-medium text-gray-500">Status</dt>
        <dd>
          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
            company.account_status === 'active' ? 'bg-green-100 text-green-800' :
            company.account_status === 'suspended' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>{company.account_status}</span>
        </dd>
        <dt className="font-medium text-gray-500">Tags</dt>
        <dd>{company.tags.length ? company.tags.join(', ') : '—'}</dd>
      </dl>

      {/* Company users list */}
      <div className="mt-8">
        <h3 className="mb-3 text-lg font-semibold text-gray-800">Users</h3>
        {companyUsers.length === 0 ? (
          <p className="text-sm text-gray-500">No users found.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Name</th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Email</th>
                  <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {companyUsers.map((u) => (
                  <tr key={u.user_id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">
                      <Link to={`/${String(u.user_id)}`} className="font-medium text-blue-600 hover:underline">
                        {u.display_name}
                      </Link>
                      <span className="ml-2 text-xs text-gray-400">@{u.username}</span>
                      {u.user_id === user?.id && (
                        <span className="ml-2 inline-flex items-center rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700">me</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-600">{u.email}</td>
                    <td className="px-4 py-2">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                        u.role_level >= 100 ? 'bg-purple-100 text-purple-800' :
                        u.role_level >= 30 ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>{formatRoleName(u.role_name)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

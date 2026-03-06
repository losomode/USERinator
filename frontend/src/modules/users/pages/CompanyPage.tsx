import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { companyApi } from '../api';
import { useAuth } from '../../../shared/auth/AuthProvider';
import type { Company } from '../types';

export function CompanyPage() {
  const { isCompanyAdmin } = useAuth();
  const [company, setCompany] = useState<Company | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    companyApi.getMy().then(setCompany).catch(() => setError('Failed to load company.'));
  }, []);

  if (error) return <div className="text-red-600">{error}</div>;
  if (!company) return <div>Loading company...</div>;

  return (
    <div className="max-w-2xl">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-bold">{company.name}</h2>
        {isCompanyAdmin && (
          <Link to="/company/edit" className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">
            Edit Company
          </Link>
        )}
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <dt className="font-medium text-gray-500">Industry</dt>
        <dd>{company.industry || '—'}</dd>
        <dt className="font-medium text-gray-500">Size</dt>
        <dd>{company.company_size || '—'}</dd>
        <dt className="font-medium text-gray-500">Website</dt>
        <dd>{company.website ? <a href={company.website} className="text-blue-600">{company.website}</a> : '—'}</dd>
        <dt className="font-medium text-gray-500">Phone</dt>
        <dd>{company.phone || '—'}</dd>
        <dt className="font-medium text-gray-500">Status</dt>
        <dd>{company.account_status}</dd>
        <dt className="font-medium text-gray-500">Tags</dt>
        <dd>{company.tags.length ? company.tags.join(', ') : '—'}</dd>
      </dl>
    </div>
  );
}

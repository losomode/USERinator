import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { companyApi } from '../api';
import type { Company, UpdateCompanyInput } from '../types';
import { PermissionGuard } from '../../../shared/permissions';

export function CompanyEditPage() {
  const navigate = useNavigate();
  const [company, setCompany] = useState<Company | null>(null);
  const [form, setForm] = useState<UpdateCompanyInput>({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    companyApi.getMy().then((c) => {
      setCompany(c);
      setForm({
        name: c.name,
        address: c.address,
        phone: c.phone,
        website: c.website,
        industry: c.industry,
        company_size: c.company_size,
        logo_url: c.logo_url,
        billing_contact_email: c.billing_contact_email,
        notes: c.notes,
      });
    }).catch(() => setError('Failed to load company.'));
  }, []);

  const handleChange = (field: keyof UpdateCompanyInput, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company) return;
    setSaving(true);
    try {
      await companyApi.update(company.id, form);
      navigate('/company');
    } catch {
      setError('Failed to save changes.');
    } finally {
      setSaving(false);
    }
  };

  if (error && !company) return <div className="text-red-600">{error}</div>;
  if (!company) return <div>Loading company...</div>;

  const fields: { label: string; key: keyof UpdateCompanyInput; type?: string }[] = [
    { label: 'Company Name', key: 'name' },
    { label: 'Address', key: 'address' },
    { label: 'Phone', key: 'phone' },
    { label: 'Website', key: 'website', type: 'url' },
    { label: 'Industry', key: 'industry' },
    { label: 'Company Size', key: 'company_size' },
    { label: 'Logo URL', key: 'logo_url', type: 'url' },
    { label: 'Billing Contact Email', key: 'billing_contact_email', type: 'email' },
    { label: 'Notes', key: 'notes' },
  ];

  return (
    <PermissionGuard 
      permission="can_edit_company"
      fallback={
        <div className="max-w-2xl">
          <h2 className="mb-4 text-2xl font-bold">Edit Company</h2>
          <p className="text-gray-500">You don't have permission to edit company information.</p>
        </div>
      }
    >
      <div className="max-w-2xl">
        <h2 className="mb-4 text-2xl font-bold">Edit Company</h2>
        {error && <div className="mb-4 text-red-600">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map(({ label, key, type }) => (
          <div key={key}>
            <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
            <input
              type={type ?? 'text'}
              value={(form[key] as string) ?? ''}
              onChange={(e) => handleChange(key, e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        ))}

        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button type="button" onClick={() => navigate('/company')} className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </form>
    </div>
    </PermissionGuard>
  );
}

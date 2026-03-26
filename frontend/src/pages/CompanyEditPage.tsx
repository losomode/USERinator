import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { companiesApi } from '../api';
import type { Company, UpdateCompanyInput } from '../types';

export function CompanyEditPage(): React.JSX.Element {
  // When navigated from /companies/:id/edit, `id` is defined and we fetch by id.
  // When navigated from /company/edit, `id` is undefined and we fall back to getMy().
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [company, setCompany] = useState<Company | null>(null);
  const [form, setForm] = useState<UpdateCompanyInput>({});
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetch = id ? companiesApi.get(Number(id)) : companiesApi.getMy();
    fetch
      .then((c) => {
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
          account_status: c.account_status,
        });
      })
      .catch(() => setError('Failed to load company.'));
  }, [id]);

  // After saving, return to the company detail page we came from
  const backLink = id ? `/companies/${id}` : '/company';

  const handleChange = (field: keyof UpdateCompanyInput, value: string): void => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!company) return;
    setSaving(true);
    try {
      await companiesApi.update(company.id, form);
      navigate(backLink);
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
    { label: 'Website', key: 'website' },
    { label: 'Industry', key: 'industry' },
    { label: 'Company Size', key: 'company_size' },
    { label: 'Logo URL', key: 'logo_url', type: 'url' },
    { label: 'Billing Contact Email', key: 'billing_contact_email', type: 'email' },
    { label: 'Notes', key: 'notes' },
  ];

  return (
    <div className="max-w-2xl">
      <h2 className="mb-4 text-2xl font-bold">Edit Company</h2>
      {error && <div className="mb-4 text-red-600">{error}</div>}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
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
          <button type="button" onClick={() => navigate(backLink)} className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

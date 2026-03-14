import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { companiesApi } from '../api';
import type { CreateCompanyInput } from '../types';

export function CompanyCreatePage(): React.JSX.Element {
  const navigate = useNavigate();
  const [form, setForm] = useState<CreateCompanyInput>({ name: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field: keyof CreateCompanyInput, value: string): void => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!form.name.trim()) {
      setError('Company name is required.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const created = await companiesApi.create(form);
      navigate(`/companies/${String(created.id)}`);
    } catch {
      setError('Failed to create company.');
    } finally {
      setSaving(false);
    }
  };

  const fields: { label: string; key: keyof CreateCompanyInput; type?: string; required?: boolean }[] = [
    { label: 'Company Name', key: 'name', required: true },
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
    <div className="max-w-2xl">
      <h2 className="mb-4 text-2xl font-bold">Add Company</h2>
      {error && <div className="mb-4 text-red-600">{error}</div>}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        {fields.map(({ label, key, type, required }) => (
          <div key={key}>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              {label}
              {required && <span className="text-red-500"> *</span>}
            </label>
            <input
              type={type ?? 'text'}
              value={(form[key] as string) ?? ''}
              onChange={(e) => handleChange(key, e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
              required={required}
            />
          </div>
        ))}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saving}
            className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Creating...' : 'Create Company'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/companies')}
            className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

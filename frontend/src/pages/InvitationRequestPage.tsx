import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { invitationsApi, rolesApi, companiesApi } from '../api';
import type { Role, Company } from '../types';

export function InvitationRequestPage(): React.JSX.Element {
  const navigate = useNavigate();
  const [roles, setRoles] = useState<Role[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [email, setEmail] = useState('');
  const [companyId, setCompanyId] = useState<number | ''>('');
  const [roleId, setRoleId] = useState<number | ''>('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    rolesApi.list().then(setRoles).catch(() => {});
    companiesApi.list().then(setCompanies).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!companyId || !roleId) {
      setError('Company and role are required.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await invitationsApi.create({
        email,
        company: companyId as number,
        requested_role: roleId as number,
        message,
      });
      navigate('/invitations');
    } catch {
      setError('Failed to submit invitation request.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h2 className="mb-4 text-2xl font-bold">Request Invitation</h2>
      {error && <div className="mb-4 text-red-600">{error}</div>}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <div>
          <label htmlFor="inv-email" className="mb-1 block text-sm font-medium text-gray-700">Email</label>
          <input
            id="inv-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="inv-company" className="mb-1 block text-sm font-medium text-gray-700">Company</label>
          <select
            id="inv-company"
            value={companyId}
            onChange={(e) => setCompanyId(Number(e.target.value))}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Select a company</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="inv-role" className="mb-1 block text-sm font-medium text-gray-700">Requested Role</label>
          <select
            id="inv-role"
            value={roleId}
            onChange={(e) => setRoleId(Number(e.target.value))}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="">Select a role</option>
            {roles.map((r) => (
              <option key={r.id} value={r.id}>{r.role_name}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="inv-message" className="mb-1 block text-sm font-medium text-gray-700">Message (optional)</label>
          <textarea
            id="inv-message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>

        <div className="flex gap-3">
          <button type="submit" disabled={submitting} className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">
            {submitting ? 'Submitting...' : 'Submit Request'}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50">
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { invitationsApi, rolesApi, companiesApi, usersApi } from '../api';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import type { Role, Company } from '../types';
import { formatRoleName } from '../types';

const PLATFORM_ROLE_THRESHOLD = 75;

export function InvitationRequestPage(): React.JSX.Element {
  const { user } = useAuth();
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [email, setEmail] = useState('');
  const [companyId, setCompanyId] = useState<number | ''>('');
  const [roleId, setRoleId] = useState<number | ''>('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [successResult, setSuccessResult] = useState<{
    message: string;
    provisioned?: { username: string; temp_password: string; note: string } | null;
    provisionError?: string;
  } | null>(null);

  // Track whether the company was auto-filled (company-scoped user)
  const [companyLocked, setCompanyLocked] = useState(false);
  const [lockedCompanyName, setLockedCompanyName] = useState('');

  useEffect(() => {
    rolesApi.list().then(setAllRoles).catch(() => {});
    companiesApi.list().then(setCompanies).catch(() => {});

    // Fetch own profile to get company_id for auto-fill
    usersApi.me().then((profile) => {
      const myLevel = profile.role_level ?? 0;
      if (myLevel < PLATFORM_ROLE_THRESHOLD && profile.company) {
      const cId = typeof profile.company === 'object' ? profile.company.id : profile.company;
        if (cId) {
          setCompanyId(cId);
          setCompanyLocked(true);
          setLockedCompanyName(profile.company_name ?? (typeof profile.company === 'object' ? profile.company.name : ''));
        }
      }
    }).catch(() => {/* best-effort */});
  }, []);

  const myLevel = user?.role_level ?? 0;
  // Invitations are for company roles only (< PLATFORM_ROLE_THRESHOLD) and <= requester's level
  const roles = allRoles.filter(
    (r) => r.role_level < PLATFORM_ROLE_THRESHOLD && r.role_level <= myLevel,
  );

  const isAdmin = myLevel >= 100;

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!companyId || !roleId) {
      setError('Company and role are required.');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const result = await invitationsApi.create({
        email,
        company: companyId as number,
        requested_role: roleId as number,
        message,
      });
      const companyName = companies.find((c) => c.id === companyId)?.name ?? String(companyId);

      if (isAdmin) {
        // Admin: invitation was auto-approved and account may already be created
        setSuccessResult({
          message: `Invitation for ${email} to join ${companyName} was sent and automatically approved.`,
          provisioned: result.provisioned_user,
          provisionError: result.provision_error,
        });
      } else {
        setSuccessResult({
          message: `Invitation submitted for ${email} to join ${companyName}. A Sighthound admin will review and approve the request. Once approved, the user will receive an email with their login details.`,
        });
      }
      // Reset form
      setEmail('');
      setCompanyId(companyLocked ? companyId : '');
      setRoleId('');
      setMessage('');
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string; email?: string[] } } })?.response?.data?.detail ??
        (err as { response?: { data?: { email?: string[] } } })?.response?.data?.email?.[0] ??
        'Failed to submit invitation.';
      setError(String(detail));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h2 className="mb-1 text-2xl font-bold">Invite New User</h2>
      <p className="mb-4 text-sm text-gray-500">
        {isAdmin
          ? 'As an admin, invitations are sent and approved immediately — the account is created right away.'
          : 'Submit an invitation for someone to join a company. A Sighthound admin will review and approve it, then the user will receive an email with their account credentials.'}
      </p>

      {successResult && (
        <div className={`mb-4 rounded border p-4 ${
          successResult.provisioned ? 'border-green-200 bg-green-50' :
          successResult.provisionError ? 'border-yellow-200 bg-yellow-50' :
          'border-green-200 bg-green-50'
        }`}>
          <p className="text-sm font-medium text-green-800">✓ {successResult.message}</p>

          {successResult.provisioned && (
            <>
              <p className="mt-2 text-sm text-green-700">
                <strong>Username:</strong> {successResult.provisioned.username}
              </p>
              <p className="text-sm text-green-700">
                <strong>Temporary Password:</strong>{' '}
                <code className="rounded bg-green-100 px-1 font-mono">{successResult.provisioned.temp_password}</code>
              </p>
              <p className="mt-1 text-xs text-green-600">{successResult.provisioned.note}</p>
              <p className="mt-0.5 text-xs text-green-600">A welcome email has also been sent (if SMTP is configured).</p>
            </>
          )}

          {successResult.provisionError && (
            <p className="mt-2 text-sm text-yellow-700">⚠ {successResult.provisionError}</p>
          )}

          <button
            className="mt-3 text-sm text-green-700 underline"
            onClick={() => setSuccessResult(null)}
          >
            Send another invitation
          </button>
        </div>
      )}

      {!successResult && (
        <>
          {error && (
            <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
          )}

          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div>
              <label htmlFor="inv-email" className="mb-1 block text-sm font-medium text-gray-700">
                Email to Invite <span className="text-red-500">*</span>
              </label>
              <input
                id="inv-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                placeholder="newuser@example.com"
              />
            </div>

<div>
              <label htmlFor="inv-company" className="mb-1 block text-sm font-medium text-gray-700">
                Company {!companyLocked && <span className="text-red-500">*</span>}
              </label>
              {companyLocked ? (
                <div className="mt-1 rounded border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
                  {lockedCompanyName || `Company #${String(companyId)}`}
                  <span className="ml-2 text-xs text-gray-400">(your company)</span>
                </div>
              ) : (
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
              )}
            </div>

            <div>
              <label htmlFor="inv-role" className="mb-1 block text-sm font-medium text-gray-700">
                Role <span className="text-red-500">*</span>
              </label>
              <select
                id="inv-role"
                value={roleId}
                onChange={(e) => setRoleId(Number(e.target.value))}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">Select a role</option>
                {roles.map((r) => (
                  <option key={r.id} value={r.id}>{formatRoleName(r.role_name)}</option>
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
              <button
                type="submit"
                disabled={submitting}
                className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {submitting ? 'Submitting…' : 'Send Invitation'}
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { invitationsApi } from '../api';
import type { Invitation } from '../types';
import { formatRoleName } from '../types';

interface ProvisionedUser {
  username: string;
  temp_password: string;
  note: string;
}

interface ApproveResult {
  invitationId: number;
  email: string;
  provisioned: ProvisionedUser | null;
  error?: string;
}

export function InvitationReviewPage(): React.JSX.Element {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [error, setError] = useState('');
  const [reviewNotes, setReviewNotes] = useState<Record<number, string>>({});
  const [processing, setProcessing] = useState<number | null>(null);
  const [results, setResults] = useState<ApproveResult[]>([]);

  const load = (): void => {
    invitationsApi.list({ status: 'PENDING' })
      .then(setInvitations)
      .catch(() => setError('Failed to load invitations.'));
  };

  useEffect(load, []);

  const handleAction = async (inv: Invitation, action: 'approve' | 'reject'): Promise<void> => {
    setProcessing(inv.id);
    try {
      if (action === 'approve') {
        const data = await invitationsApi.approve(inv.id, reviewNotes[inv.id]) as unknown as Record<string, unknown>;
        setResults((prev) => [
          ...prev,
          {
            invitationId: inv.id,
            email: inv.email,
            provisioned: (data.provisioned_user as ProvisionedUser | null) ?? null,
            error: data.provision_error as string | undefined,
          },
        ]);
      } else {
        await invitationsApi.reject(inv.id, reviewNotes[inv.id]);
      }
      setInvitations((prev) => prev.filter((i) => i.id !== inv.id));
    } catch {
      setError(`Failed to ${action} invitation.`);
    } finally {
      setProcessing(null);
    }
  };

  return (
    <div className="max-w-3xl">
      <h2 className="mb-4 text-2xl font-bold">Review Invitations</h2>
      {error && <div className="mb-4 text-red-600">{error}</div>}

      {/* Show results from recent approvals */}
      {results.length > 0 && (
        <div className="mb-6 space-y-3">
          {results.map((r) => (
            <div
              key={r.invitationId}
              className={`rounded border p-4 ${
                r.provisioned ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'
              }`}
            >
              {r.provisioned ? (
                <>
                  <p className="text-sm font-semibold text-green-800">
                    ✓ Account created for {r.email}
                  </p>
                  <p className="mt-1 text-sm text-green-700">
                    <strong>Username:</strong> {r.provisioned.username}
                  </p>
                  <p className="text-sm text-green-700">
                    <strong>Temporary Password:</strong>{' '}
                    <code className="rounded bg-green-100 px-1 font-mono">
                      {r.provisioned.temp_password}
                    </code>
                  </p>
                  <p className="mt-1 text-xs text-green-600">{r.provisioned.note}</p>
                  <p className="mt-1 text-xs text-green-600">
                    A welcome email has also been sent to {r.email} (if SMTP is configured).
                  </p>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-yellow-800">⚠ Invitation approved for {r.email}</p>
                  <p className="mt-1 text-sm text-yellow-700">{r.error}</p>
                </>
              )}
            </div>
          ))}
          <button
            className="text-sm text-gray-500 underline"
            onClick={() => setResults([])}
          >
            Clear results
          </button>
        </div>
      )}

      {invitations.length === 0 && !error && results.length === 0 && (
        <p className="text-gray-500">No pending invitations.</p>
      )}

      <div className="space-y-4">
        {invitations.map((inv) => (
          <div key={inv.id} className="rounded border border-gray-200 p-4">
            <div className="mb-2 flex items-start justify-between">
              <div>
                <span className="font-medium">{inv.email}</span>
                {inv.requested_role_name && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                    {formatRoleName(inv.requested_role_name)}
                  </span>
                )}
                {inv.company_name && (
                  <span className="ml-2 text-xs text-gray-500">→ {inv.company_name}</span>
                )}
                <div className="mt-0.5 text-xs text-gray-400">
                  Requested {new Date(inv.requested_at).toLocaleDateString()}
                </div>
              </div>
              <span className="rounded bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
                {inv.status}
              </span>
            </div>

            {inv.message && <p className="mb-2 text-sm text-gray-600">{inv.message}</p>}

            <div className="mb-2">
              <input
                type="text"
                placeholder="Review notes (optional)"
                value={reviewNotes[inv.id] ?? ''}
                onChange={(e) => setReviewNotes((prev) => ({ ...prev, [inv.id]: e.target.value }))}
                className="w-full rounded border border-gray-300 px-3 py-1 text-sm"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => void handleAction(inv, 'approve')}
                disabled={processing === inv.id}
                className="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700 disabled:opacity-50"
              >
                {processing === inv.id ? 'Processing…' : 'Approve'}
              </button>
              <button
                onClick={() => void handleAction(inv, 'reject')}
                disabled={processing === inv.id}
                className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700 disabled:opacity-50"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

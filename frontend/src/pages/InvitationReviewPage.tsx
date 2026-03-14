import { useEffect, useState } from 'react';
import { invitationsApi } from '../api';
import type { Invitation } from '../types';

export function InvitationReviewPage(): React.JSX.Element {
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [error, setError] = useState('');
  const [reviewNotes, setReviewNotes] = useState<Record<number, string>>({});
  const [processing, setProcessing] = useState<number | null>(null);

  const load = (): void => {
    invitationsApi.list({ status: 'PENDING' })
      .then(setInvitations)
      .catch(() => setError('Failed to load invitations.'));
  };

  useEffect(load, []);

  const handleAction = async (id: number, action: 'approve' | 'reject'): Promise<void> => {
    setProcessing(id);
    try {
      const fn = action === 'approve' ? invitationsApi.approve : invitationsApi.reject;
      await fn(id, reviewNotes[id]);
      setInvitations((prev) => prev.filter((inv) => inv.id !== id));
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

      {invitations.length === 0 && !error && (
        <p className="text-gray-500">No pending invitations.</p>
      )}

      <div className="space-y-4">
        {invitations.map((inv) => (
          <div key={inv.id} className="rounded border border-gray-200 p-4">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <span className="font-medium">{inv.email}</span>
                <span className="ml-2 text-xs text-gray-500">Requested {new Date(inv.requested_at).toLocaleDateString()}</span>
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
                onClick={() => void handleAction(inv.id, 'approve')}
                disabled={processing === inv.id}
                className="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700 disabled:opacity-50"
              >
                Approve
              </button>
              <button
                onClick={() => void handleAction(inv.id, 'reject')}
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

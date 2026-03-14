import { useEffect, useState } from 'react';
import { preferencesApi } from '../api';
import type { UserPreferences } from '../types';

export function PreferencesPage(): React.JSX.Element {
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    preferencesApi.get().then(setPrefs).catch(() => setError('Failed to load preferences.'));
  }, []);

  const handleChange = (field: keyof UserPreferences, value: string | boolean): void => {
    setPrefs((prev) => prev ? { ...prev, [field]: value } : prev);
    setSaved(false);
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!prefs) return;
    setSaving(true);
    try {
      const updated = await preferencesApi.update(prefs);
      setPrefs(updated);
      setSaved(true);
    } catch {
      setError('Failed to save preferences.');
    } finally {
      setSaving(false);
    }
  };

  if (error && !prefs) return <div className="text-red-600">{error}</div>;
  if (!prefs) return <div>Loading preferences...</div>;

  return (
    <div className="max-w-lg">
      <h2 className="mb-4 text-2xl font-bold">Preferences</h2>
      {error && <div className="mb-4 text-red-600">{error}</div>}
      {saved && <div className="mb-4 text-green-600">Preferences saved.</div>}

      <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
        <div>
          <label htmlFor="pref-timezone" className="mb-1 block text-sm font-medium text-gray-700">Timezone</label>
          <input
            id="pref-timezone"
            type="text"
            value={prefs.timezone}
            onChange={(e) => handleChange('timezone', e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label htmlFor="pref-language" className="mb-1 block text-sm font-medium text-gray-700">Language</label>
          <input
            id="pref-language"
            type="text"
            value={prefs.language}
            onChange={(e) => handleChange('language', e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={prefs.notification_email}
              onChange={(e) => handleChange('notification_email', e.target.checked)}
              className="rounded border-gray-300"
            />
            Email notifications
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={prefs.notification_in_app}
              onChange={(e) => handleChange('notification_in_app', e.target.checked)}
              className="rounded border-gray-300"
            />
            In-app notifications
          </label>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>
      </form>
    </div>
  );
}

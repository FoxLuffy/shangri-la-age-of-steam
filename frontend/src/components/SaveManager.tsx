import { useCallback, useEffect, useState } from 'react';
import { createSave, getSave, loadSave, deleteSave } from '../api';
import type { SaveMeta } from '../api';

interface SaveManagerProps {
  characterId: number;
  onLoad: () => void;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export default function SaveManager({ characterId, onLoad }: SaveManagerProps) {
  const [save, setSave] = useState<SaveMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const meta = await getSave(characterId);
      setSave(meta);
    } catch {
      // 404 (or any failure) means there is no save slot yet.
      setSave(null);
    }
  }, [characterId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    try {
      await createSave(characterId);
      await refresh();
    } catch {
      setError('Failed to save.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoad = async () => {
    if (!save) return;
    if (!window.confirm('Load your saved state? This overwrites your current unsaved progress.')) return;
    setLoading(true);
    setError(null);
    try {
      await loadSave(characterId);
      onLoad();
    } catch {
      setError('Failed to load.');
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!save) return;
    if (!window.confirm('Delete this save slot permanently? This cannot be undone.')) return;
    setLoading(true);
    setError(null);
    try {
      await deleteSave(characterId);
      setSave(null);
    } catch {
      setError('Failed to delete.');
    } finally {
      setLoading(false);
    }
  };

  const btnBase = 'flex-1 py-2 text-xs uppercase tracking-wider border transition-colors disabled:opacity-40 disabled:cursor-not-allowed';

  return (
    <div className="flex flex-col gap-3 p-4 border border-amber-900/30 bg-slate-800/30">
      <div>
        <div className="text-sm uppercase text-amber-400">Save State</div>
        <div className="text-xs text-amber-600/70 mt-1">
          One save slot per character. Saving overwrites it; loading restores your world, inventory, and quests.
        </div>
      </div>

      <div className="text-xs text-amber-200/90 border border-amber-900/20 bg-slate-950/40 p-2">
        {save ? (
          <span>
            <span className="text-amber-400">{save.name}</span>
            <span className="text-amber-600/60"> — {formatTimestamp(save.created_at)}</span>
          </span>
        ) : (
          <span className="text-slate-500 italic">No save yet for this character.</span>
        )}
      </div>

      {error && <div className="text-xs text-red-400">{error}</div>}

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={loading}
          className={`${btnBase} bg-amber-900/40 border-amber-500 text-amber-400 hover:bg-amber-800/60`}
        >
          {loading ? '...' : 'Save Now'}
        </button>
        <button
          onClick={handleLoad}
          disabled={loading || !save}
          className={`${btnBase} bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700`}
        >
          Load
        </button>
        <button
          onClick={handleDelete}
          disabled={loading || !save}
          className={`${btnBase} bg-red-900/30 border-red-800 text-red-300 hover:bg-red-900/50`}
        >
          Delete
        </button>
      </div>
    </div>
  );
}

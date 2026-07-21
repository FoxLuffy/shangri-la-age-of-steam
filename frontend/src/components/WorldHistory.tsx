import { useEffect, useState } from 'react';
import { fetchHistory, type LedgerEntry } from '../api';

export default function WorldHistory({ onClose }: { onClose: () => void }) {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await fetchHistory(100);
      setEntries(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredEntries = entries.filter((e) =>
    e.action.toLowerCase().includes(search.toLowerCase()) ||
    e.narration.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="absolute inset-0 bg-slate-950/95 backdrop-blur z-50 flex flex-col font-mono text-slate-100 p-6 shadow-2xl overflow-hidden rounded-xl border border-amber-900/40">
      <div className="flex items-center justify-between border-b border-amber-800/40 pb-4 mb-4">
        <h2 className="text-xl font-bold text-amber-500 uppercase tracking-widest flex items-center gap-2">
          <span>📜</span>
          <span>World History Ledger</span>
        </h2>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-rose-400 transition-colors bg-slate-900 border border-slate-700 px-3 py-1 rounded"
        >
          Close [X]
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search ledger entries..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-slate-900 border border-amber-800/50 rounded p-2 text-sm focus:outline-none focus:border-amber-500 text-amber-100 placeholder-slate-500"
        />
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {isLoading ? (
          <div className="text-amber-500 animate-pulse text-sm">Loading archives...</div>
        ) : filteredEntries.length === 0 ? (
          <div className="text-slate-500 text-sm">No ledger entries found.</div>
        ) : (
          filteredEntries.map((entry) => (
            <div key={entry.id} className="bg-slate-900/60 border border-slate-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-amber-400 font-bold text-sm">Action: {entry.action}</span>
                <span className="text-xs text-slate-500">
                  {new Date(entry.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed mb-3 whitespace-pre-wrap">
                {entry.narration}
              </p>
              
              {((entry.state_updates && Object.keys(entry.state_updates).length > 0) || (entry.events && entry.events.length > 0)) && (
                <div className="bg-slate-950 p-2 rounded text-xs text-slate-400 font-mono">
                  {entry.events && entry.events.length > 0 && (
                    <div className="mb-1">
                      <strong className="text-sky-400">Events:</strong>{' '}
                      {entry.events.map(ev => typeof ev === 'string' ? ev : JSON.stringify(ev)).join(' | ')}
                    </div>
                  )}
                  {entry.state_updates && Object.keys(entry.state_updates).length > 0 && (
                    <div>
                      <strong className="text-emerald-400">Updates:</strong>{' '}
                      {JSON.stringify(entry.state_updates)}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

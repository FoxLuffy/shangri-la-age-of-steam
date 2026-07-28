import { useState, useEffect, useCallback } from 'react';
import { createGuild, inviteGuild, fetchMyGuild } from '../api';
import type { MyGuildData } from '../api';

export default function GuildPanel({ characterId, onClose }: { characterId: number, onClose: () => void }) {
  const [data, setData] = useState<MyGuildData | null>(null);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [inviteId, setInviteId] = useState('');
  const [error, setError] = useState('');

  const loadGuild = useCallback(async () => {
    try {
      setLoading(true);
      const d = await fetchMyGuild(characterId);
      setData(d);
    } catch {
      setError('Failed to load guild.');
    } finally {
      setLoading(false);
    }
  }, [characterId]);

  useEffect(() => {
    if (characterId) loadGuild();
  }, [characterId, loadGuild]);

  const handleCreate = async () => {
    setError('');
    try {
      setLoading(true);
      await createGuild(characterId, name, desc);
      // Refetch so the new guild is shown immediately — no "close and reopen".
      await loadGuild();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error creating guild');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!data?.guild) return;
    setError('');
    try {
      setLoading(true);
      await inviteGuild(characterId, data.guild.id, parseInt(inviteId));
      setInviteId('');
      await loadGuild();
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error inviting to guild');
    } finally {
      setLoading(false);
    }
  };

  const guild = data?.guild;

  return (
    <div className="absolute inset-0 bg-slate-950/80 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-amber-900 rounded-xl p-6 w-full max-w-lg shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">✕</button>
        <h2 className="text-xl font-bold text-amber-500 mb-4 flex items-center gap-2">
          <span>🛡️</span> Guild Management
        </h2>

        {error && <div className="text-rose-400 text-sm mb-4">{error}</div>}
        {loading && !guild && <div className="text-slate-400 text-sm mb-4">Loading...</div>}

        {guild ? (
          <div className="flex flex-col gap-4">
            <div className="bg-slate-800 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-amber-400">{guild.name}</h3>
                <span className="text-xs text-amber-300">Treasury: {guild.treasury} coins</span>
              </div>
              {guild.description && <p className="text-sm text-slate-300 mt-1">{guild.description}</p>}
            </div>

            <div className="bg-slate-800 p-4 rounded-lg">
              <h3 className="text-md font-semibold text-slate-200 mb-2">Members ({data!.members.length})</h3>
              <ul className="flex flex-col gap-1">
                {data!.members.map((m) => (
                  <li key={m.id} className="text-sm text-slate-300 flex items-center gap-2">
                    <span>{m.name}</span>
                    {m.is_leader && <span className="text-[10px] uppercase bg-amber-700 text-amber-100 px-1.5 py-0.5 rounded">Leader</span>}
                  </li>
                ))}
              </ul>
            </div>

            {data!.is_leader && (
              <div className="bg-slate-800 p-4 rounded-lg">
                <h3 className="text-md font-semibold text-slate-200 mb-2">Invite Character</h3>
                <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2" placeholder="Character ID" value={inviteId} onChange={e => setInviteId(e.target.value)} />
                <button onClick={handleInvite} disabled={loading || !inviteId} className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded disabled:opacity-50">
                  Invite
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="text-md font-semibold text-slate-200 mb-2">Create New Guild</h3>
            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2" placeholder="Guild Name" value={name} onChange={e => setName(e.target.value)} />
            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2" placeholder="Description" value={desc} onChange={e => setDesc(e.target.value)} />
            <button onClick={handleCreate} disabled={loading || !name} className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded disabled:opacity-50">
              Create Guild
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

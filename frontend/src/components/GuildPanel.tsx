import { useState, useEffect } from 'react';
import { fetchGuildTreasury, createGuild, inviteGuild } from '../api';
import { useGameStore } from '../stores/gameStore';

export default function GuildPanel({ characterId, onClose }: { characterId: number, onClose: () => void }) {
  const [guildData, setGuildData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [inviteId, setInviteId] = useState('');
  const [error, setError] = useState('');

  // Fetch character first to get guild_id? 
  // In a real app we'd get this from gameStore.
  // Assuming character doesn't have a guild yet, we allow creation.
  
  const handleCreate = async () => {
    try {
      setLoading(true);
      await createGuild(characterId, name, desc);
      setError('Guild created! Close and reopen to view.');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error creating guild');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!guildData) return;
    try {
      setLoading(true);
      await inviteGuild(characterId, guildData.guild.id, parseInt(inviteId));
      setError('Invite sent!');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Error inviting to guild');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950/80 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-amber-900 rounded-xl p-6 w-full max-w-lg shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">✕</button>
        <h2 className="text-xl font-bold text-amber-500 mb-4 flex items-center gap-2">
          <span>🛡️</span> Guild Management
        </h2>
        
        {error && <div className="text-rose-400 text-sm mb-4">{error}</div>}

        <div className="flex flex-col gap-4">
          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="text-md font-semibold text-slate-200 mb-2">Create New Guild</h3>
            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2" placeholder="Guild Name" value={name} onChange={e => setName(e.target.value)} />
            <input className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2" placeholder="Description" value={desc} onChange={e => setDesc(e.target.value)} />
            <button onClick={handleCreate} disabled={loading} className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded">
              Create Guild
            </button>
          </div>
          
          <div className="bg-slate-800 p-4 rounded-lg">
            <h3 className="text-md font-semibold text-slate-200 mb-2">Invite Character</h3>
            <input type="number" className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2" placeholder="Character ID" value={inviteId} onChange={e => setInviteId(e.target.value)} />
            <button onClick={handleInvite} disabled={loading} className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded">
              Invite
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

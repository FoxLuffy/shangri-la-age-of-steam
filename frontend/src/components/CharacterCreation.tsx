import { useState } from 'react';
import { createCharacter } from '../api';

interface Preset {
  id: string;
  name: string;
  desc: string;
}

const PRESETS: Preset[] = [
  { id: 'Wanderer', name: 'Wanderer', desc: 'Balanced stats. A mysterious wanderer.' },
  { id: 'Aristocrat', name: 'Aristocrat', desc: 'High charm. Uses influence to get ahead.' },
  { id: 'Scrapper', name: 'Scrapper', desc: 'High strength. Survives in the lower decks.' },
  { id: 'Alchemist', name: 'Alchemist', desc: 'High intellect. Masters steam and chemicals.' },
];

export default function CharacterCreation({ onComplete }: { onComplete: (charId: number) => void }) {
  const [name, setName] = useState('');
  const [preset, setPreset] = useState('Wanderer');
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const char = await createCharacter(name, preset);
      onComplete(char.id);
    } catch (e) {
      console.error(e);
      alert('Failed to create character');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full h-full text-amber-100 bg-slate-900 font-mono">
      <div className="border border-amber-900/50 bg-slate-950 p-8 shadow-[0_0_15px_rgba(217,119,6,0.3)] w-full max-w-md">
        <h1 className="text-3xl font-bold mb-6 text-amber-500 border-b border-amber-900/50 pb-2 text-center uppercase tracking-widest">
          Manifest
        </h1>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm text-amber-600/70 uppercase mb-2">Name</label>
            <input 
              type="text" 
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-900 border border-amber-900/50 p-2 text-amber-100 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600"
              placeholder="Enter your name..."
            />
          </div>

          <div>
            <label className="block text-sm text-amber-600/70 uppercase mb-2">Class Preset</label>
            <div className="space-y-2">
              {PRESETS.map(p => (
                <div 
                  key={p.id}
                  onClick={() => setPreset(p.id)}
                  className={`p-3 border cursor-pointer transition-colors ${preset === p.id ? 'border-amber-500 bg-amber-900/20' : 'border-amber-900/30 hover:border-amber-700'}`}
                >
                  <div className="font-bold text-amber-400">{p.name}</div>
                  <div className="text-xs text-amber-200/50">{p.desc}</div>
                </div>
              ))}
            </div>
          </div>

          <button 
            onClick={handleCreate}
            disabled={!name.trim() || loading}
            className="w-full bg-amber-900/50 border border-amber-500 text-amber-400 p-3 uppercase tracking-wider hover:bg-amber-800/50 disabled:opacity-50 transition-colors mt-8"
          >
            {loading ? 'Embarking...' : 'Begin Journey'}
          </button>
        </div>
      </div>
    </div>
  );
}

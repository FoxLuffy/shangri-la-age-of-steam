import { useState, useEffect } from 'react';
import { createCharacter, generateGear, fetchSessions } from '../api';
import type { Character } from '../api';

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

export default function CharacterCreation({ onComplete, userId }: { onComplete: (charId: number) => void, userId?: number | null }) {
  const [name, setName] = useState('');
  const [preset, setPreset] = useState('Wanderer');
  const [backstory, setBackstory] = useState('');
  const [gearPrompt, setGearPrompt] = useState('');
  const [showTutorials, setShowTutorials] = useState(true);
  const [loading, setLoading] = useState(false);
  
  const [gearList, setGearList] = useState<any[]>([]);
  const [gearAttempts, setGearAttempts] = useState(0);
  const [generatingGear, setGeneratingGear] = useState(false);
  
  const [sessions, setSessions] = useState<Character[]>([]);
  const [fetchingSessions, setFetchingSessions] = useState(false);
  const [showCreationForm, setShowCreationForm] = useState(false);

  useEffect(() => {
    if (userId) {
      setFetchingSessions(true);
      fetchSessions(userId).then(chars => {
        setSessions(chars);
        if (chars.length === 0) {
          setShowCreationForm(true);
        }
      }).catch(err => {
        console.error(err);
      }).finally(() => {
        setFetchingSessions(false);
      });
    } else {
      setShowCreationForm(true);
    }
  }, [userId]);

  const handleGenerateGear = async () => {
    if (!gearPrompt.trim() || gearAttempts >= 3) return;
    setGeneratingGear(true);
    try {
      const items = await generateGear(preset, gearPrompt);
      setGearList(items);
      setGearAttempts(prev => prev + 1);
    } catch (e) {
      console.error(e);
      alert('Failed to generate gear');
    } finally {
      setGeneratingGear(false);
    }
  };

  const handleCreate = async () => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const char = await createCharacter(name, preset, backstory, gearPrompt, showTutorials, gearList, userId);
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
      <div className="border border-amber-900/50 bg-slate-950 p-8 shadow-[0_0_15px_rgba(217,119,6,0.3)] w-full max-w-md max-h-screen overflow-y-auto">
        {!showCreationForm ? (
          <div>
            <h1 className="text-3xl font-bold mb-6 text-amber-500 border-b border-amber-900/50 pb-2 text-center uppercase tracking-widest">
              Select Session
            </h1>
            {fetchingSessions ? (
              <div className="text-center text-amber-500 py-4">Fetching previous sessions...</div>
            ) : (
              <div className="space-y-4">
                {sessions.map(s => (
                  <div key={s.id} className="border border-amber-900/50 p-4 hover:border-amber-500 cursor-pointer bg-slate-900" onClick={() => onComplete(s.id)}>
                    <div className="font-bold text-amber-400 text-xl">{s.name}</div>
                    <div className="text-xs text-amber-200/50 mt-1">Class: {s.character_class}</div>
                  </div>
                ))}
                <button 
                  onClick={() => setShowCreationForm(true)}
                  className="w-full bg-amber-900/30 border border-amber-700 text-amber-500 p-3 uppercase hover:bg-amber-800/40 transition-colors mt-4"
                >
                  Create New Character
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
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

          <div>
            <label className="block text-sm text-amber-600/70 uppercase mb-2">Custom Backstory (Optional)</label>
            <textarea 
              value={backstory}
              onChange={(e) => setBackstory(e.target.value)}
              className="w-full bg-slate-900 border border-amber-900/50 p-2 text-amber-100 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 resize-none h-20"
              placeholder="Leave blank to use the class preset backstory, or write your own origin..."
            />
          </div>

          <div>
            <div className="flex justify-between items-end mb-2">
              <label className="block text-sm text-amber-600/70 uppercase">Request Gear</label>
              <span className="text-xs text-amber-700">{3 - gearAttempts} attempts remaining</span>
            </div>
            <textarea 
              value={gearPrompt}
              onChange={(e) => setGearPrompt(e.target.value)}
              className="w-full bg-slate-900 border border-amber-900/50 p-2 text-amber-100 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 resize-none h-20"
              placeholder="Describe what gear or equipment you're carrying..."
              disabled={gearAttempts >= 3}
            />
            <button 
              onClick={handleGenerateGear}
              disabled={!gearPrompt.trim() || gearAttempts >= 3 || generatingGear}
              className="w-full mt-2 bg-amber-900/30 border border-amber-700 text-amber-500 p-2 uppercase text-sm hover:bg-amber-800/40 disabled:opacity-50 transition-colors"
            >
              {generatingGear ? 'Fabricating...' : 'Generate Gear'}
            </button>
            
            {gearList.length > 0 && (
              <div className="mt-4 p-3 border border-amber-900/50 bg-slate-900">
                <div className="text-xs text-amber-600 uppercase mb-2">Manifested Items:</div>
                <ul className="space-y-2">
                  {gearList.map((item, idx) => (
                    <li key={idx} className="text-sm border-l-2 border-amber-700 pl-2">
                      <div className="text-amber-400 font-bold">{item.name} <span className="text-amber-700 text-xs">x{item.quantity || 1}</span></div>
                      <div className="text-amber-200/60 text-xs">{item.description}</div>
                      <div className="text-amber-600/50 text-[10px] uppercase mt-1">{item.category}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 mt-4 border border-amber-900/30 p-3 bg-slate-900/50">
            <input 
              type="checkbox" 
              id="tutorials"
              checked={showTutorials}
              onChange={(e) => setShowTutorials(e.target.checked)}
              className="w-4 h-4 accent-amber-600"
            />
            <label htmlFor="tutorials" className="text-xs text-amber-500/80 cursor-pointer select-none">
              Enable Interactive Tutorials (Recommended for new players)
            </label>
          </div>

          <button 
            onClick={handleCreate}
            disabled={!name.trim() || loading}
            className="w-full bg-amber-900/50 border border-amber-500 text-amber-400 p-3 uppercase tracking-wider hover:bg-amber-800/50 disabled:opacity-50 transition-colors mt-8"
          >
            {loading ? 'Embarking...' : 'Begin Journey'}
          </button>
          {sessions.length > 0 && (
            <button 
              onClick={() => setShowCreationForm(false)}
              className="w-full mt-2 text-sm text-amber-600/70 hover:text-amber-500 uppercase transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
        </>
        )}
      </div>
    </div>
  );
}

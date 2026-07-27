import { useState, useEffect } from 'react';
import { createCharacter, generateGear, fetchSessions, fetchMainQuests, generateMainQuest } from '../api';
import type { Character, MainQuestInput, MainQuestPreset } from '../api';

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

const ORIGINS: Preset[] = [
  { id: 'Foundry Orphan', name: 'Foundry Orphan', desc: 'Grants Soot-Stained Rag, Scrap Metal, and favor with Foreman Ironfist.' },
  { id: 'Aristocratic Heir', name: 'Aristocratic Heir', desc: 'Grants Signet Ring, Fine Wine, and favor with Lord Sterling.' },
  { id: 'Guild Apprentice', name: 'Guild Apprentice', desc: 'Grants Apprentice Badge, Basic Tools, and favor with Master Craftsman.' },
  { id: 'Smuggler\'s Ward', name: 'Smuggler\'s Ward', desc: 'Grants Lockpick Set, Smuggler\'s Map, and favor with Sly The Fox.' },
  { id: 'Automata Tinkerer', name: 'Automata Tinkerer', desc: 'Grants Spare Gear, Wrench, and favor with Tinkerer Tom.' },
];

export default function CharacterCreation({ onComplete, userId }: { onComplete: (charId: number) => void, userId?: number | null }) {
  const [name, setName] = useState('');
  const [preset, setPreset] = useState('Wanderer');
  const [origin, setOrigin] = useState('Foundry Orphan');
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
  const [step, setStep] = useState(0);
  const STEPS = ['Name & Class', 'Backstory & Origin', 'Equipment', 'Main Quest'];

  // Main quest (CR10)
  const [mqPresets, setMqPresets] = useState<MainQuestPreset[]>([]);
  const [mainQuest, setMainQuest] = useState<MainQuestInput | null>(null);
  const [generatingMQ, setGeneratingMQ] = useState(false);
  const [mqTheme, setMqTheme] = useState('');

  useEffect(() => {
    fetchMainQuests().then(setMqPresets).catch(console.error);
  }, []);

  const handleGenerateMainQuest = async () => {
    setGeneratingMQ(true);
    try {
      setMainQuest(await generateMainQuest(preset, origin, backstory, mqTheme));
    } catch (e) {
      console.error(e);
      alert('Failed to generate main quest');
    } finally {
      setGeneratingMQ(false);
    }
  };

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
      const char = await createCharacter(name, preset, origin, backstory, gearPrompt, showTutorials, gearList, userId, mainQuest);
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
                    <div className="text-xs text-amber-200/40 mt-1 flex justify-between gap-2">
                      {s.location_name && <span>📍 {s.location_name}</span>}
                      <span className="ml-auto">
                        {s.has_save && s.last_saved
                          ? `Saved: ${new Date(s.last_saved).toLocaleString()}`
                          : 'No save yet'}
                      </span>
                    </div>
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
            
            <div className="grid grid-cols-4 gap-1 mb-5">
              {STEPS.map((label, i) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => { if (i === 0 || name.trim()) setStep(i); }}
                  className={`py-2 text-[10px] uppercase tracking-wide border ${step === i ? 'border-amber-500 bg-amber-600 text-slate-950 font-bold' : 'border-amber-900/40 text-amber-500/70 hover:border-amber-700'}`}
                >
                  {i + 1}. {label}
                </button>
              ))}
            </div>

            <div className="space-y-6 min-h-[16rem]">
              {step === 0 && (
                <>
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
                </>
              )}

              {step === 1 && (
                <>
                  <div>
                    <label className="block text-sm text-amber-600/70 uppercase mb-2">Origin Background</label>
                    <div className="space-y-2">
                      {ORIGINS.map(o => (
                        <div
                          key={o.id}
                          onClick={() => setOrigin(o.id)}
                          className={`p-3 border cursor-pointer transition-colors ${origin === o.id ? 'border-amber-500 bg-amber-900/20' : 'border-amber-900/30 hover:border-amber-700'}`}
                        >
                          <div className="font-bold text-amber-400">{o.name}</div>
                          <div className="text-xs text-amber-200/50">{o.desc}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm text-amber-600/70 uppercase mb-2">Custom Backstory (Optional)</label>
                    <textarea
                      value={backstory}
                      onChange={(e) => setBackstory(e.target.value)}
                      className="w-full bg-slate-900 border border-amber-900/50 p-2 text-amber-100 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 resize-none h-24"
                      placeholder="Leave blank to use the class preset backstory, or write your own origin..."
                    />
                  </div>
                </>
              )}

              {step === 2 && (
                <div>
                  <div className="flex justify-between items-end mb-2">
                    <label className="block text-sm text-amber-600/70 uppercase">Request Gear</label>
                    <span className="text-xs text-amber-700">{3 - gearAttempts} attempts remaining</span>
                  </div>
                  <textarea
                    value={gearPrompt}
                    onChange={(e) => setGearPrompt(e.target.value)}
                    className="w-full bg-slate-900 border border-amber-900/50 p-2 text-amber-100 focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600 resize-none h-24"
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
              )}

              {step === 3 && (
                <>
                  <div>
                    <label className="block text-sm text-amber-600/70 uppercase mb-2">Main Quest</label>
                    <input
                      type="text"
                      value={mqTheme}
                      onChange={(e) => setMqTheme(e.target.value)}
                      className="w-full bg-slate-900 border border-amber-900/50 p-2 mb-2 text-amber-100 text-sm focus:outline-none focus:border-amber-600 focus:ring-1 focus:ring-amber-600"
                      placeholder="Optional: describe a theme for Generate (e.g. 'revenge against the Syndicate')"
                    />
                    <div className="flex gap-2 mb-3">
                      <button
                        type="button"
                        onClick={() => setMainQuest(null)}
                        className={`flex-1 py-2 text-xs uppercase border ${!mainQuest ? 'border-amber-500 bg-amber-900/20 text-amber-400' : 'border-amber-900/30 text-amber-200/60'}`}
                      >
                        None
                      </button>
                      <button
                        type="button"
                        onClick={() => { if (mqPresets.length) setMainQuest(mqPresets[Math.floor(Math.random() * mqPresets.length)]); }}
                        className="flex-1 py-2 text-xs uppercase border border-amber-900/30 text-amber-200/80 hover:border-amber-700"
                      >
                        Random
                      </button>
                      <button
                        type="button"
                        onClick={handleGenerateMainQuest}
                        disabled={generatingMQ}
                        className="flex-1 py-2 text-xs uppercase border border-amber-700 text-amber-400 hover:bg-amber-900/30 disabled:opacity-50"
                      >
                        {generatingMQ ? '...' : 'Generate'}
                      </button>
                    </div>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {mqPresets.map(q => (
                        <div
                          key={q.id}
                          onClick={() => setMainQuest(q)}
                          className={`p-3 border cursor-pointer transition-colors ${mainQuest?.title === q.title ? 'border-amber-500 bg-amber-900/20' : 'border-amber-900/30 hover:border-amber-700'}`}
                        >
                          <div className="font-bold text-amber-400">{q.title}</div>
                          <div className="text-xs text-amber-200/50">{q.description}</div>
                        </div>
                      ))}
                    </div>
                    {mainQuest && (
                      <div className="mt-2 text-xs text-amber-300 border border-amber-900/30 bg-slate-900/40 p-2">
                        <div className="font-bold">Chosen: {mainQuest.title}</div>
                        <ol className="list-decimal ml-4 mt-1 text-amber-200/70">
                          {mainQuest.stages.map((s, i) => <li key={i}>{s}</li>)}
                        </ol>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-3 border border-amber-900/30 p-3 bg-slate-900/50">
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
                </>
              )}
            </div>

            <div className="flex gap-2 mt-6">
              {step > 0 && (
                <button
                  type="button"
                  onClick={() => setStep(step - 1)}
                  className="flex-1 border border-amber-900/40 text-amber-500 p-3 uppercase tracking-wider hover:bg-amber-900/20 transition-colors"
                >
                  Back
                </button>
              )}
              {step < STEPS.length - 1 ? (
                <button
                  type="button"
                  onClick={() => setStep(step + 1)}
                  disabled={step === 0 && !name.trim()}
                  className="flex-1 bg-amber-900/40 border border-amber-600 text-amber-400 p-3 uppercase tracking-wider hover:bg-amber-800/50 disabled:opacity-50 transition-colors"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleCreate}
                  disabled={!name.trim() || loading}
                  className="flex-1 bg-amber-900/50 border border-amber-500 text-amber-400 p-3 uppercase tracking-wider hover:bg-amber-800/50 disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Embarking...' : 'Begin Journey'}
                </button>
              )}
            </div>
            {sessions.length > 0 && (
              <button
                onClick={() => setShowCreationForm(false)}
                className="w-full mt-2 text-sm text-amber-600/70 hover:text-amber-500 uppercase transition-colors"
              >
                Cancel
              </button>
            )}
        </>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { sendAction, fetchState } from '../api';

interface Message {
  type: 'action' | 'narration' | 'system' | 'event';
  content: string;
  mood?: string;
}

interface Location {
  id: string;
  name: string;
  description: string;
  npcs: string[];
}

interface NPC {
  id: string;
  name: string;
  traits: string[];
  current_dialogue?: string | null;
  disposition: number;
  memories: { key: string; value: string }[];
}

interface WorldState {
  current_location: Location;
  active_npcs: NPC[];
  global_event?: string | null;
  world_memories: { key: string; value: string }[];
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [worldState, setWorldState] = useState<WorldState | null>(null);
  const [input, setInput] = useState('');
  const [mood, setMood] = useState('');
  const [isExploration, setIsExploration] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Load initial state and add introductory text
  useEffect(() => {
    const initGame = async () => {
      try {
        const state = await fetchState();
        setWorldState(state);
        setMessages([
          {
            type: 'system',
            content: 'Narrator initialized. Welcome to the steam-driven wastes of Shangri-la.'
          },
          {
            type: 'narration',
            content: `You find yourself in: ${state.current_location.name}. ${state.current_location.description}`
          }
        ]);
      } catch (err) {
        setMessages([
          {
            type: 'system',
            content: 'System error: Unable to connect to the steam core (backend).'
          }
        ]);
      }
    };
    initGame();
  }, []);

  // Auto scroll to bottom of chat
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const playerActionText = input;
    setInput('');
    setIsLoading(true);

    // Add player action to log
    setMessages((prev) => [
      ...prev,
      { type: 'action', content: playerActionText, mood: mood || undefined }
    ]);

    try {
      const result = await sendAction(playerActionText, mood || undefined, isExploration);
      
      // Add narration response
      setMessages((prev) => [
        ...prev,
        { type: 'narration', content: result.narration }
      ]);

      // Add any dynamic events
      if (result.events && result.events.length > 0) {
        result.events.forEach((evt: any) => {
          const desc = typeof evt === 'string' ? evt : evt.description || JSON.stringify(evt);
          setMessages((prev) => [
            ...prev,
            { type: 'event', content: `[Event Triggered] ${desc}` }
          ]);
        });
      }

      // Re-fetch world state to synchronize UI
      const updatedState = await fetchState();
      setWorldState(updatedState);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { type: 'system', content: 'Inference core connection failed. Pressure loss in steam pipes.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to color disposition bar and text
  const getDispositionColor = (disp: number) => {
    if (disp <= -0.3) return 'text-rose-400';
    if (disp >= 0.3) return 'text-emerald-400';
    return 'text-amber-400';
  };

  const getDispositionBg = (disp: number) => {
    if (disp <= -0.3) return 'bg-rose-500';
    if (disp >= 0.3) return 'bg-emerald-500';
    return 'bg-amber-500';
  };

  const getDispositionLabel = (disp: number) => {
    if (disp <= -0.6) return 'Hostile';
    if (disp <= -0.2) return 'Wary';
    if (disp <= 0.2) return 'Neutral';
    if (disp <= 0.6) return 'Friendly';
    return 'Loyal';
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row gap-6 p-4 md:p-6 bg-zinc-950 text-zinc-100 font-mono h-full">
      {/* Sidebar: World State and NPCs */}
      <div className="w-full md:w-80 flex flex-col gap-6 flex-shrink-0">
        
        {/* Connection status and global settings */}
        <div className="bg-zinc-900/60 backdrop-blur-md border border-zinc-800 rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span className="text-xs uppercase tracking-widest text-amber-500 font-bold">Steam Core Active</span>
          </div>
          {worldState?.global_event && (
            <div className="mt-2 bg-amber-950/30 border border-amber-500/30 rounded-lg p-3 text-xs">
              <div className="font-bold text-amber-400 uppercase mb-1">Global Event:</div>
              <p className="text-zinc-300">{worldState.global_event}</p>
            </div>
          )}
        </div>

        {/* Location Information */}
        <div className="bg-zinc-900/60 backdrop-blur-md border border-zinc-800 rounded-xl p-5 flex flex-col gap-3 shadow-2xl">
          <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-amber-500">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
            </svg>
            <h2 className="text-lg font-bold text-amber-500 uppercase tracking-wider">Location</h2>
          </div>
          {worldState ? (
            <div>
              <h3 className="font-bold text-zinc-100 text-md uppercase">{worldState.current_location.name}</h3>
              <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{worldState.current_location.description}</p>
            </div>
          ) : (
            <div className="animate-pulse flex space-x-4">
              <div className="flex-1 space-y-4 py-1">
                <div className="h-4 bg-zinc-800 rounded w-3/4"></div>
                <div className="space-y-2">
                  <div className="h-3 bg-zinc-800 rounded"></div>
                  <div className="h-3 bg-zinc-800 rounded w-5/6"></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* NPC List */}
        <div className="flex-1 bg-zinc-900/60 backdrop-blur-md border border-zinc-800 rounded-xl p-5 flex flex-col gap-4 shadow-2xl overflow-y-auto max-h-[50vh] md:max-h-none">
          <div className="flex items-center gap-2 border-b border-zinc-800 pb-3">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-amber-500">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" />
            </svg>
            <h2 className="text-lg font-bold text-amber-500 uppercase tracking-wider">Present NPCs</h2>
          </div>
          
          {worldState ? (
            worldState.active_npcs.length > 0 ? (
              <div className="flex flex-col gap-4">
                {worldState.active_npcs.map((npc) => (
                  <div key={npc.id} className="border border-zinc-800 rounded-lg p-3 bg-zinc-950/40 flex flex-col gap-2 transition hover:border-zinc-700">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-zinc-200 text-sm uppercase">{npc.name}</span>
                      <span className={`text-[10px] font-bold uppercase ${getDispositionColor(npc.disposition)}`}>
                        {getDispositionLabel(npc.disposition)}
                      </span>
                    </div>

                    {/* Traits */}
                    <div className="flex flex-wrap gap-1">
                      {npc.traits.map((trait, idx) => (
                        <span key={idx} className="text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-400 uppercase">
                          {trait}
                        </span>
                      ))}
                    </div>

                    {/* Disposition Bar */}
                    <div className="w-full bg-zinc-800 rounded-full h-1 mt-1">
                      <div 
                        className={`h-1 rounded-full ${getDispositionBg(npc.disposition)}`}
                        style={{ width: `${Math.min(Math.max((npc.disposition + 1) * 50, 0), 100)}%` }}
                      ></div>
                    </div>

                    {/* NPC Memories */}
                    {npc.memories && npc.memories.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-zinc-900 text-[10px] text-zinc-500">
                        <span className="font-semibold text-zinc-400 block mb-0.5">Memories:</span>
                        {npc.memories.map((m, mIdx) => (
                          <div key={mIdx} className="leading-tight mb-1">
                            <span className="text-amber-600/70">{m.key}:</span> <span className="text-zinc-400">{m.value}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500 italic">No characters are currently active here.</p>
            )
          ) : (
            <div className="animate-pulse space-y-3">
              <div className="h-8 bg-zinc-800 rounded"></div>
              <div className="h-8 bg-zinc-800 rounded"></div>
            </div>
          )}
        </div>
      </div>

      {/* Main Panel: Terminal Chat Feed and Action Box */}
      <div className="flex-1 flex flex-col bg-zinc-900/60 backdrop-blur-md border border-zinc-800 rounded-xl shadow-2xl overflow-hidden h-[80vh] md:h-auto">
        {/* Terminal Header */}
        <div className="bg-zinc-950 border-b border-zinc-800 px-6 py-4 flex justify-between items-center flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-red-600"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-600"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-green-600"></div>
            <span className="text-xs text-zinc-500 tracking-widest uppercase ml-2">narrative-terminal-v2.0</span>
          </div>
          <div className="text-xs text-amber-500/80 font-bold uppercase tracking-wider">
            {worldState?.current_location.name || "SHANGRI-LA"}
          </div>
        </div>

        {/* Scrollable Feed */}
        <div ref={scrollRef} className="flex-grow p-6 overflow-y-auto space-y-6 flex flex-col">
          {messages.map((msg, i) => {
            if (msg.type === 'action') {
              return (
                <div key={i} className="self-end max-w-[85%] flex flex-col items-end gap-1">
                  <div className="text-[10px] text-zinc-500 flex gap-2">
                    {msg.mood && <span className="text-amber-500/60 font-semibold">[Mood: {msg.mood}]</span>}
                    <span>You</span>
                  </div>
                  <div className="bg-amber-600 text-zinc-950 font-semibold px-4 py-2.5 rounded-lg rounded-tr-none shadow-md text-sm border border-amber-500/30 whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>
              );
            }
            if (msg.type === 'narration') {
              return (
                <div key={i} className="self-start max-w-[90%] flex flex-col gap-1">
                  <span className="text-[10px] text-zinc-500">Narrator</span>
                  <div className="bg-zinc-950/70 border border-zinc-800 text-zinc-200 px-5 py-4 rounded-xl rounded-tl-none shadow-lg text-sm leading-relaxed whitespace-pre-wrap border-l-4 border-l-amber-500">
                    {msg.content}
                  </div>
                </div>
              );
            }
            if (msg.type === 'event') {
              return (
                <div key={i} className="mx-auto max-w-[80%] my-1 text-center bg-cyan-950/20 border border-cyan-800/30 rounded-lg py-2 px-4 text-xs text-cyan-300">
                  {msg.content}
                </div>
              );
            }
            // system
            return (
              <div key={i} className="mx-auto max-w-[80%] my-1 text-center bg-zinc-850/40 border border-zinc-800/60 rounded-lg py-1.5 px-4 text-xs text-zinc-500">
                {msg.content}
              </div>
            );
          })}

          {isLoading && (
            <div className="self-start max-w-[90%] flex flex-col gap-1 animate-pulse">
              <span className="text-[10px] text-zinc-500">Narrator</span>
              <div className="bg-zinc-950/30 border border-zinc-900 text-zinc-500 px-5 py-4 rounded-xl rounded-tl-none text-sm flex items-center gap-3">
                <svg className="animate-spin h-5 w-5 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Generating narrative response... Release valve pressure building...</span>
              </div>
            </div>
          )}
        </div>

        {/* Input area */}
        <form onSubmit={handleSendMessage} className="bg-zinc-950 border-t border-zinc-850 p-4 flex flex-col gap-3 flex-shrink-0">
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Input box */}
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe your actions (e.g. 'I sit down next to Barnaby and order a rum')"
              disabled={isLoading}
              className="flex-1 bg-zinc-900 border border-zinc-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-lg px-4 py-2.5 text-sm outline-none transition disabled:opacity-50 text-zinc-100 placeholder-zinc-600"
            />
            
            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-zinc-950 font-bold px-6 py-2.5 rounded-lg text-sm transition shadow-lg hover:shadow-amber-500/20 disabled:opacity-50 disabled:pointer-events-none uppercase tracking-wider flex items-center justify-center gap-2 flex-shrink-0"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path d="M3.105 2.289a.75.75 0 0 0-.826.95l1.414 4.925A1.5 1.5 0 0 0 5.135 9.25h6.115a.75.75 0 0 1 0 1.5H5.135a1.5 1.5 0 0 0-1.442 1.086l-1.414 4.926a.75.75 0 0 0 .826.95 28.896 28.896 0 0 0 15.293-7.154.75.75 0 0 0 0-1.115A28.897 28.897 0 0 0 3.105 2.289Z" />
              </svg>
              <span>Vent Steam</span>
            </button>
          </div>

          {/* Action modifiers */}
          <div className="flex flex-wrap items-center justify-between gap-4 mt-1 border-t border-zinc-900 pt-3 text-xs text-zinc-400">
            <div className="flex items-center gap-6">
              {/* Mood selector */}
              <div className="flex items-center gap-2">
                <span className="text-zinc-500">Character Mood:</span>
                <select
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                  disabled={isLoading}
                  className="bg-zinc-900 border border-zinc-800 focus:border-amber-500 rounded px-2.5 py-1 outline-none text-zinc-300 transition text-xs cursor-pointer"
                >
                  <option value="">Default (None)</option>
                  <option value="Cautious">Cautious</option>
                  <option value="Determined">Determined</option>
                  <option value="Friendly">Friendly</option>
                  <option value="Hostile">Hostile / Threatening</option>
                  <option value="Sarcastic">Sarcastic</option>
                  <option value="Stealthy">Stealthy</option>
                  <option value="Tense">Tense</option>
                </select>
              </div>

              {/* Exploration Mode Checkbox */}
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={isExploration}
                  onChange={(e) => setIsExploration(e.target.checked)}
                  disabled={isLoading}
                  className="accent-amber-500 cursor-pointer h-3.5 w-3.5 rounded border-zinc-800 bg-zinc-900 focus:ring-0 focus:ring-offset-0"
                />
                <span className="text-zinc-500">Exploration Focus</span>
              </label>
            </div>
            
            <div className="text-[10px] text-zinc-600 tracking-wider">
              SHANGRI-LA RPG v2.0 // SYSTEM LOAD: NORMAL
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

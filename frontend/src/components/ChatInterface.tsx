import { useState, useEffect, useRef, type FormEvent } from 'react';
import { 
  sendAction, 
  fetchWorldState, 
  resetWorldState, 
  type Location as LocationType, 
  type NPC as NPCType,
  type GetStateResponse
} from '../api';

import AudioManager from './AudioManager';

interface Message {
  id: string;
  sender: 'user' | 'narrator' | 'system';
  content: string;
  timestamp: string;
  mood?: string;
  isExploration?: boolean;
  stateUpdates?: any;
  events?: any[];
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedMood, setSelectedMood] = useState<string>('');
  const [isExploration, setIsExploration] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentLocationId, setCurrentLocationId] = useState<string>('1');
  const [currentLocation, setCurrentLocation] = useState<LocationType | null>(null);
  const [allLocations, setAllLocations] = useState<LocationType[]>([]);
  const [activeNpcs, setActiveNpcs] = useState<NPCType[]>([]);
  const [globalEvent, setGlobalEvent] = useState<string>('');
  const [expandedNpcId, setExpandedNpcId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('Connected to vLLM Engine');
  
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll message feed
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Load initial state on component mount
  useEffect(() => {
    loadState();
  }, []);

  const loadState = async () => {
    try {
      const data: GetStateResponse = await fetchWorldState();
      if (data.state) {
        if (data.state.current_location_id) {
          setCurrentLocationId(data.state.current_location_id);
        }
        if (data.state.current_location) {
          setCurrentLocation(data.state.current_location);
        }
        if (data.state.active_npcs) {
          setActiveNpcs(data.state.active_npcs);
        }
        if (data.state.global_event) {
          setGlobalEvent(data.state.global_event);
        }
      }
      if (data.all_locations) {
        setAllLocations(data.all_locations);
        const match = data.all_locations.find(l => l.id === (data.state?.current_location_id || '1'));
        if (match) setCurrentLocation(match);
      }

      // Initial welcome message if messages list is empty
      if (messages.length === 0) {
        const welcomeMessage: Message = {
          id: 'msg-0',
          sender: 'narrator',
          content: `Welcome to Shangri-la: Age of Steam.\n\nYou stand in ${data.state?.current_location?.name || 'The Rusty Anchor Tavern'}. ${data.state?.current_location?.description || 'Steam discharges softly from the overhead copper valves.'}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages([welcomeMessage]);
      }
    } catch (err) {
      console.error('Failed to fetch world state:', err);
      setStatusMessage('Warning: Could not connect to backend state server.');
    }
  };

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const actionText = input.trim();
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: actionText,
      timestamp: now,
      mood: selectedMood || undefined,
      isExploration
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const narratorMsgId = `narrator-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: narratorMsgId,
          sender: 'narrator',
          content: '',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      const response = await sendAction({
        action_text: actionText,
        current_location_id: currentLocationId,
        mood: selectedMood || undefined,
        is_exploration: isExploration
      }, (chunk) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === narratorMsgId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      });

      if (response) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === narratorMsgId
              ? { ...msg, stateUpdates: response.state_updates, events: response.events }
              : msg
          )
        );
      }

      await loadState();
    } catch (error: any) {
      console.error('Error sending message:', error);
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'system',
        content: `Error: Failed to process action (${error.message || 'Network error'}). Ensure backend server is running on port 8003.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetWorld = async () => {
    if (!window.confirm('Reset world state back to initial seed data?')) return;
    setIsLoading(true);
    try {
      await resetWorldState();
      setMessages([]);
      await loadState();
      setStatusMessage('World state reset successfully.');
    } catch (err) {
      console.error('Reset failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocationSwitch = async (newLocId: string) => {
    if (newLocId === currentLocationId) return;
    setCurrentLocationId(newLocId);
    const locMatch = allLocations.find(l => l.id === newLocId);
    if (locMatch) setCurrentLocation(locMatch);

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const travelText = `Travel to ${locMatch ? locMatch.name : 'new area'}`;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: travelText,
      timestamp: now
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const narratorMsgId = `narrator-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: narratorMsgId,
          sender: 'narrator',
          content: '',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);

      const response = await sendAction({
        action_text: travelText,
        current_location_id: newLocId,
        is_exploration: true
      }, (chunk) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === narratorMsgId
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      });

      if (response) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === narratorMsgId
              ? { ...msg, stateUpdates: response.state_updates, events: response.events }
              : msg
          )
        );
      }

      await loadState();
    } catch (err) {
      console.error('Travel failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getDispositionColor = (disposition: number) => {
    if (disposition > 0.2) return 'bg-emerald-500 text-emerald-100';
    if (disposition < -0.2) return 'bg-rose-500 text-rose-100';
    return 'bg-amber-500 text-amber-100';
  };

  const moods = [
    { id: '', label: 'Neutral 😐' },
    { id: 'cautious', label: 'Cautious 🔍' },
    { id: 'bold', label: 'Bold ⚔️' },
    { id: 'inquisitive', label: 'Inquisitive 📜' },
    { id: 'tense', label: 'Tense ⚡' }
  ];

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 rounded-xl border border-amber-900/40 shadow-2xl overflow-hidden font-mono relative">
      <AudioManager locationId={currentLocationId} />
      {/* Top Header */}
      <header className="bg-slate-900/90 border-b border-amber-800/40 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-amber-950 border border-amber-500 flex items-center justify-center text-amber-400 font-bold shadow-inner">
            ⚙️
          </div>
          <div>
            <h1 className="text-xl font-extrabold tracking-wider copper-gradient-text uppercase">
              Shangri-la: Age of Steam
            </h1>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-led"></span>
              <span>{statusMessage}</span>
            </div>
          </div>
        </div>

        {globalEvent && (
          <div className="hidden lg:flex items-center gap-2 bg-amber-950/40 border border-amber-700/30 px-3 py-1.5 rounded-full text-xs text-amber-300">
            <span className="text-amber-500">📢</span>
            <span className="truncate max-w-md">{globalEvent}</span>
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={handleResetWorld}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-amber-400 border border-amber-600/40 rounded transition-all flex items-center gap-1"
            title="Reset Database State"
          >
            🔄 Reset World
          </button>
        </div>
      </header>

      {/* Location Bar */}
      <div className="bg-slate-900/60 border-b border-slate-800 px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-amber-500 font-semibold">📍 LOCATION:</span>
          <span className="text-slate-200 font-bold text-sm">
            {currentLocation ? currentLocation.name : 'Loading location...'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-400">Fast Travel:</span>
          {allLocations.map((loc) => (
            <button
              key={loc.id}
              onClick={() => handleLocationSwitch(loc.id)}
              className={`px-2.5 py-1 rounded transition-colors ${
                loc.id === currentLocationId
                  ? 'bg-amber-600 text-slate-950 font-bold shadow'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {loc.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Side: Interactive Narration Stream */}
        <div className="flex-1 flex flex-col p-4 overflow-hidden border-r border-slate-800">
          <div
            ref={scrollRef}
            className="flex-1 overflow-y-auto space-y-4 pr-2 scrollbar-thin scrollbar-thumb-amber-700"
          >
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col max-w-3xl ${
                  msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
                }`}
              >
                <div className="flex items-center gap-2 text-[10px] text-slate-400 mb-1 px-1">
                  <span className="font-bold uppercase tracking-wider text-amber-500">
                    {msg.sender === 'user' ? '👤 Player Action' : msg.sender === 'narrator' ? '📜 Narrator' : '⚠️ System'}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {msg.mood && (
                    <span className="bg-amber-950 text-amber-300 border border-amber-700/50 px-1.5 py-0.5 rounded text-[9px]">
                      Mood: {msg.mood}
                    </span>
                  )}
                  {msg.isExploration && (
                    <span className="bg-sky-950 text-sky-300 border border-sky-700/50 px-1.5 py-0.5 rounded text-[9px]">
                      🔍 Exploration Mode
                    </span>
                  )}
                </div>

                <div
                  className={`p-4 rounded-xl text-sm leading-relaxed whitespace-pre-wrap shadow-md border ${
                    msg.sender === 'user'
                      ? 'bg-amber-950/40 border-amber-700/50 text-amber-100 rounded-tr-none'
                      : msg.sender === 'system'
                      ? 'bg-rose-950/30 border-rose-800/40 text-rose-200 rounded-tl-none'
                      : 'bg-slate-900/90 border-slate-700/60 text-slate-200 rounded-tl-none'
                  }`}
                >
                  {msg.content}

                  {msg.events && msg.events.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-amber-900/40 flex flex-wrap gap-2 text-xs">
                      <span className="font-semibold text-amber-400">⚡ Dynamic Events:</span>
                      {msg.events.map((ev: any, idx: number) => (
                        <span key={idx} className="bg-amber-900/60 text-amber-200 px-2 py-0.5 rounded border border-amber-700/50">
                          {typeof ev === 'string' ? ev : JSON.stringify(ev)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-3 text-amber-400/80 p-3 bg-slate-900/60 rounded-lg border border-amber-800/30 w-fit">
                <div className="w-4 h-4 rounded-full border-2 border-amber-500 border-t-transparent animate-spin"></div>
                <span className="text-xs animate-pulse">Consulting the Steam Engine & vLLM...</span>
              </div>
            )}
          </div>

          <form onSubmit={handleSendMessage} className="mt-4 pt-3 border-t border-slate-800 flex flex-col gap-3">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-slate-400 mr-1">Player Mood:</span>
                {moods.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setSelectedMood(m.id)}
                    className={`px-2.5 py-1 rounded text-[11px] transition-colors ${
                      selectedMood === m.id
                        ? 'bg-amber-600 text-slate-950 font-bold shadow'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>

              <label className="flex items-center gap-2 cursor-pointer bg-slate-900 border border-slate-700 px-2.5 py-1 rounded hover:border-sky-500 transition-all">
                <input
                  type="checkbox"
                  checked={isExploration}
                  onChange={(e) => setIsExploration(e.target.checked)}
                  className="accent-sky-500"
                />
                <span className="text-sky-300 font-semibold">🔍 Exploration Mode</span>
              </label>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your action (e.g., 'Inspect the copper pressure gauge' or 'Talk to Barnaby')..."
                className="flex-1 bg-slate-900 border border-amber-800/50 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-amber-500 text-amber-100 placeholder-slate-500 shadow-inner"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-slate-950 font-bold px-6 py-3 rounded-lg text-sm transition-all shadow-lg flex items-center gap-2"
              >
                <span>SEND</span>
                <span>➔</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right Side: Active NPCs */}
        <aside className="w-full md:w-80 bg-slate-900/40 p-4 border-t md:border-t-0 md:border-l border-slate-800 flex flex-col gap-4 overflow-y-auto">
          <div className="bg-slate-900/80 border border-amber-900/40 p-4 rounded-xl shadow-md">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Environment Overview</span>
              <span>🧭</span>
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              {currentLocation ? currentLocation.description : 'Select a location to explore.'}
            </p>
          </div>

          <div className="flex-1 flex flex-col gap-3">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center justify-between">
              <span>Active NPCs ({activeNpcs.length})</span>
              <span>👥</span>
            </h3>

            {activeNpcs.length === 0 ? (
              <div className="text-xs text-slate-500 italic p-3 bg-slate-900/50 rounded-lg border border-slate-800">
                No active NPCs detected in this vicinity.
              </div>
            ) : (
              activeNpcs.map((npc) => (
                <div
                  key={npc.id}
                  className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-3 shadow-md flex flex-col gap-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-100">{npc.name}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${getDispositionColor(npc.disposition)}`}>
                      {npc.disposition > 0.2 ? 'Friendly' : npc.disposition < -0.2 ? 'Hostile' : 'Neutral'}
                    </span>
                  </div>

                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        npc.disposition > 0 ? 'bg-emerald-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(10, ((npc.disposition + 1) / 2) * 100))}%` }}
                    ></div>
                  </div>

                  <div className="flex flex-wrap gap-1 mt-1">
                    {npc.traits && npc.traits.map((trait, i) => (
                      <span key={i} className="bg-slate-800 text-slate-300 text-[10px] px-2 py-0.5 rounded">
                        #{trait}
                      </span>
                    ))}
                  </div>

                  {npc.memories && npc.memories.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-800">
                      <button
                        onClick={() => setExpandedNpcId(expandedNpcId === npc.id ? null : npc.id)}
                        className="text-[11px] text-amber-400 hover:text-amber-300 flex items-center justify-between w-full"
                      >
                        <span>🧠 Persistent Memories ({npc.memories.length})</span>
                        <span>{expandedNpcId === npc.id ? '▲' : '▼'}</span>
                      </button>

                      {expandedNpcId === npc.id && (
                        <div className="mt-2 space-y-1.5">
                          {npc.memories.map((m, idx) => (
                            <div key={idx} className="bg-slate-950 p-2 rounded text-[10px] border border-slate-800">
                              <span className="font-bold text-amber-300">{m.key}: </span>
                              <span className="text-slate-300">{m.value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

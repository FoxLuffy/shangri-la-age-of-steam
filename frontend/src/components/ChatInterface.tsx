import { useState, useEffect, useRef, useMemo } from 'react';
import { 
  sendAction, 
  resetWorldState, 
  importWorldState,
  BACKEND_URL,
  useWorldStateQuery,
  useGlossaryQuery
} from '../api';
import type { NPC } from '../api';

import AudioManager from './AudioManager';
import WorldHistory from './WorldHistory';
import NarrativeStream from './NarrativeStream';
import ActionBar from './ActionBar';
import { WebSocketSync } from './WebSocketSync';
import { StateUpdateHandler } from './StateUpdateHandler';
import { useGameStore } from '../stores/gameStore';
import WorldMap from './WorldMap';
import GuildPanel from './GuildPanel';
import BulletinBoard from './BulletinBoard';
import BountyBoard from './BountyBoard';
import { audioManager } from '../utils/AudioManager';
import { ArtifactJournal } from './ArtifactJournal';
import CombatUI from './CombatUI';
import { recordActionAndMaybeAutosave, autosaveBeforeTravel, resetAutosaveCounter } from '../utils/autosave';


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

interface ChatInterfaceProps {
  characterId?: number;
  onStateUpdate?: (state: any) => void;
  onOpenCombat?: () => void;
  onOpenMinigame?: () => void;
}

export default function ChatInterface({ characterId, onStateUpdate, onOpenCombat, onOpenMinigame }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedMood, setSelectedMood] = useState<string>('');
  const [isExploration, setIsExploration] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expandedNpcId, setExpandedNpcId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('Connected to vLLM Engine');
  const [showHistory, setShowHistory] = useState(false);
  const [isMapOpen, setIsMapOpen] = useState(false);
  const [isGuildOpen, setIsGuildOpen] = useState(false);
  const [isBoardOpen, setIsBoardOpen] = useState(false);
  const [isBountyBoardOpen, setIsBountyBoardOpen] = useState(false);
  const [isJournalOpen, setIsJournalOpen] = useState(false);
  const [isEnvExpanded, setIsEnvExpanded] = useState(() => localStorage.getItem('saos_env_expanded') === 'true');
  const [clientId] = useState(() => `client-${Math.random().toString(36).substring(2, 9)}`);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // useGameStore mapped states
  const currentLocationId = useGameStore(state => state.currentLocationId);
  const currentLocation = useGameStore(state => state.currentLocation);
  const allLocations = useGameStore(state => state.allLocations);
  const activeNpcs = useGameStore(state => state.activeNpcs);
  const globalEvent = useGameStore(state => state.globalEvent);
  const combatState = useGameStore(state => state.combatState);
  const isMinigameActive = useGameStore(state => state.isMinigameActive);
  
  const setCurrentLocationId = useGameStore(state => state.setCurrentLocationId);
  const setCurrentLocation = useGameStore(state => state.setCurrentLocation);
  const setAllLocations = useGameStore(state => state.setAllLocations);
  const setActiveNpcs = useGameStore(state => state.setActiveNpcs);
  const setActivePlayers = useGameStore(state => state.setActivePlayers);
  const setIsMinigameActive = useGameStore(state => state.setIsMinigameActive);
  const setCombatState = useGameStore(state => state.setCombatState);
  const setGlobalEvent = useGameStore(state => state.setGlobalEvent);

  const { data: worldStateData, refetch: loadState } = useWorldStateQuery(characterId);
  const { data: glossaryData } = useGlossaryQuery();

  // Guaranteed world-state refresh — runs in a finally so the panes reflect post-action
  // state even if the stream handler threw first. Panes read from the store, which is synced
  // from this query; without it a travel leaves stale location/NPCs (report #3).
  const refreshWorldState = async () => {
    try {
      await loadState();
    } catch (e) {
      console.error('worldState refetch failed', e);
    }
  };

  // Sync state to gameStore on worldStateData update
  useEffect(() => {
    if (worldStateData) {
      if (worldStateData.state) {
        setCurrentLocationId(worldStateData.state.current_location_id || '1');
        setCurrentLocation(worldStateData.state.current_location || null);
        setActiveNpcs(worldStateData.state.active_npcs || []);
        setIsMinigameActive(!!worldStateData.state.active_minigame);
        setCombatState(worldStateData.state.combat_state || null);
        setGlobalEvent(worldStateData.state.global_event || '');

        if (onStateUpdate) {
          onStateUpdate(worldStateData.state);
        }

        const shouldAutoExpand = localStorage.getItem('saos_auto_expand_env') === 'true';
        if (shouldAutoExpand) {
          setIsEnvExpanded(true);
          localStorage.setItem('saos_env_expanded', 'true');
        }
      }
      if (worldStateData.all_locations) {
        setAllLocations(worldStateData.all_locations);
        const match = worldStateData.all_locations.find(l => l.id === (worldStateData.state?.current_location_id || '1'));
        if (match) setCurrentLocation(match);
      }
      if (worldStateData.active_players) {
        setActivePlayers(worldStateData.active_players);
      } else {
        setActivePlayers([]);
      }
    }
  }, [worldStateData, setCurrentLocationId, setCurrentLocation, setActiveNpcs, setIsMinigameActive, setCombatState, setGlobalEvent, setAllLocations, setActivePlayers, onStateUpdate]);

  const handleExportSave = () => {
    window.open(`${BACKEND_URL}/export`, '_blank');
  };

  const handleImportSave = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      try {
        setIsLoading(true);
        await importWorldState(e.target.files[0]);
        setStatusMessage('Save imported successfully');
        await loadState();
        setMessages([]); 
      } catch (err) {
        console.error('Import failed', err);
        setStatusMessage('Failed to import save');
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Sync messages to localStorage
  useEffect(() => {
    if (characterId && messages.length > 0) {
      localStorage.setItem(`saos_chat_history_${characterId}`, JSON.stringify(messages));
    }
  }, [messages, characterId]);

  // Load initial state on component mount
  useEffect(() => {
    // New character/session: restart the periodic-autosave cadence.
    resetAutosaveCounter();
    if (characterId) {
      const stored = localStorage.getItem(`saos_chat_history_${characterId}`);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) {
            setMessages(parsed);
          }
        } catch (e) {
          console.error("Failed to parse chat history:", e);
        }
      }
    }
    
    const handlePing = () => {
      setIsEnvExpanded(true);
      localStorage.setItem('saos_env_expanded', 'true');
    };
    window.addEventListener('saos_ping_exploration', handlePing);
    return () => window.removeEventListener('saos_ping_exploration', handlePing);
  }, [characterId]);

  useEffect(() => {
    if (currentLocationId) {
      audioManager.setAmbience(currentLocationId);
    }
  }, [currentLocationId]);

  useEffect(() => {
    const handlePeerEvent = (e: any) => {
      const msg = e.detail;
      const actionText = msg.action.action_text || 'Another player acted.';
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      
      setMessages(prev => [
        ...prev,
        {
          id: `peer-user-${Date.now()}`,
          sender: 'user',
          content: actionText,
          timestamp: now,
          mood: msg.action.mood
        },
        {
          id: `peer-narrator-${Date.now()}`,
          sender: 'narrator',
          content: msg.data.narration || '',
          timestamp: now,
          mood: msg.action.mood,
          stateUpdates: msg.data.state_updates,
          events: msg.data.events
        }
      ]);
    };
    const handleGlobalEvent = (e: any) => {
      const msg = e.detail;
      const newMsg: Message = {
        id: Date.now().toString(),
        sender: 'system',
        content: `[GLOBAL BROADCAST] ${msg.event}`,
        timestamp: msg.timestamp
      };
      setMessages(prev => [...prev, newMsg]);
    };

    window.addEventListener('saos_peer_event', handlePeerEvent);
    window.addEventListener('saos_global_event', handleGlobalEvent);
    return () => {
      window.removeEventListener('saos_peer_event', handlePeerEvent);
      window.removeEventListener('saos_global_event', handleGlobalEvent);
    };
  }, []);

  useEffect(() => {
    if (worldStateData && messages.length === 0) {
      const welcomeMessage: Message = {
        id: 'msg-0',
        sender: 'narrator',
        content: `Welcome to Shangri-la: Age of Steam.\n\nYou stand in ${worldStateData.state?.current_location?.name || 'The Rusty Anchor Tavern'}. ${worldStateData.state?.current_location?.description || 'Steam discharges softly from the overhead copper valves.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages([welcomeMessage]);
    }
  }, [worldStateData, messages.length]);

  useEffect(() => {
    const handleSystemAction = (e: any) => {
      const msg = e.detail;
      if (msg) {
        submitAction(msg, true);
      }
    };
    window.addEventListener('saos_system_action', handleSystemAction);
    return () => window.removeEventListener('saos_system_action', handleSystemAction);
  }, [isLoading]);

  // Post a concise combat result to the main log when a fight ends (report #11: results are
  // sent back to the main context).
  const prevCombatRef = useRef(false);
  useEffect(() => {
    const active = !!worldStateData?.state?.is_combat_active;
    if (prevCombatRef.current && !active) {
      const alive = (worldStateData?.state?.player_stats?.hp ?? 1) > 0;
      setMessages((prev) => [
        ...prev,
        {
          id: `combat-end-${Date.now()}`,
          sender: 'system',
          content: alive ? '⚔️ The fight is over — you are still standing.' : '⚔️ You have fallen in combat…',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
    prevCombatRef.current = active;
  }, [worldStateData]);

  const isMyTurn = useMemo(() => {
    if (!combatState || !combatState.is_active) return true;
    const { turn_order, current_turn_index } = combatState;
    if (!turn_order || current_turn_index >= turn_order.length) return true;
    const currentActor = turn_order[current_turn_index];
    return currentActor.type === 'player' && currentActor.id === characterId;
  }, [combatState, characterId]);
  
  const currentTurnActor = combatState?.turn_order?.[combatState?.current_turn_index]?.name || '';

  const submitAction = async (actionText: string, isSystem: boolean = false) => {
    if (!actionText || isLoading) return;

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: isSystem ? 'system' : 'user',
      content: actionText,
      timestamp: now,
      mood: isSystem ? undefined : selectedMood || undefined,
      isExploration: isSystem ? false : isExploration
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
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          mood: selectedMood || undefined
        }
      ]);

      const response = await sendAction({
        action_text: actionText,
        current_location_id: currentLocationId,
        mood: selectedMood || undefined,
        is_exploration: isExploration,
        context_type: isExploration ? 'Exploration' : 'Dialogue',
        client_id: clientId,
        character_id: characterId
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

      // Periodic autosave on real player actions (best-effort; never blocks).
      if (!isSystem && characterId) {
        void recordActionAndMaybeAutosave(characterId);
      }
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
      // Defense-in-depth: guarantee the panes reflect post-action state even if the stream
      // handler threw before the in-try loadState().
      await refreshWorldState();
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

    // Pre-travel autosave checkpoint (best-effort; never blocks travel).
    if (characterId) {
      await autosaveBeforeTravel(characterId);
    }

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
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          mood: selectedMood || undefined
        }
      ]);

      const response = await sendAction({
        action_text: travelText,
        current_location_id: newLocId,
        is_exploration: true,
        context_type: 'Exploration',
        client_id: clientId
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

    } catch (err) {
      console.error('Travel failed:', err);
    } finally {
      // Always refresh — even if the stream handler above threw, the panes must reflect the
      // new location and its NPCs (report #3: travel not reflected, old NPC stuck).
      await refreshWorldState();
      setIsLoading(false);
    }
  };

  const getDispositionColor = (disposition: number) => {
    if (disposition > 0.2) return 'bg-emerald-500 text-emerald-100';
    if (disposition < -0.2) return 'bg-rose-500 text-rose-100';
    return 'bg-amber-500 text-amber-100';
  };

  const renderNpcCard = (npc: NPC, engaged: boolean) => (
    <div
      key={npc.id}
      className={`bg-slate-900/90 rounded-xl p-3 shadow-md flex flex-col gap-2 border ${
        engaged ? 'border-amber-500/70 ring-1 ring-amber-500/30' : 'border-slate-700/80 opacity-80'
      }`}
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

      {expandedNpcId === npc.id ? (
        <div className="mt-2 text-xs text-amber-200/80 bg-slate-950/50 p-2 rounded italic">
          {npc.current_dialogue || 'No current dialogue.'}
        </div>
      ) : (
        <button
          onClick={() => setExpandedNpcId(npc.id)}
          className="mt-2 text-[10px] text-sky-400 hover:text-sky-300 text-left"
        >
          Show Dialogue...
        </button>
      )}
      {expandedNpcId === npc.id && (
        <button
          onClick={() => setExpandedNpcId(null)}
          className="mt-1 text-[10px] text-slate-500 hover:text-slate-400 text-left"
        >
          Hide Dialogue
        </button>
      )}
    </div>
  );

  const steamOpacity = currentLocationId === '1' ? 0.4 : currentLocationId === '2' ? 0.1 : 0.2;

  const timePeriod = worldStateData?.state?.time_period || 'Day';
  const weather = worldStateData?.state?.weather || 'Clear';
  let envClass = '';
  if (timePeriod === 'Night' || weather === 'Thunderstorm') {
    envClass = 'theme-cool';
  } else if (timePeriod === 'Day' || timePeriod === 'Dawn' || timePeriod === 'Dusk') {
    envClass = 'theme-warm';
  }

  return (
    <div className={`flex flex-col h-full bg-slate-950 text-slate-100 rounded-xl border border-amber-900/40 shadow-2xl overflow-hidden font-mono relative transition-colors duration-1000 ${envClass}`}>
      <div 
        className="pointer-events-none absolute inset-0 steam-overlay z-50 transition-opacity duration-1000"
        style={{ opacity: steamOpacity }}
      />
      <AudioManager locationId={currentLocationId} mood={selectedMood} />
      {showHistory && <WorldHistory onClose={() => setShowHistory(false)} />}
      {isMapOpen && (
        <WorldMap 
          locations={allLocations}
          currentLocationId={currentLocationId}
          characterId={characterId || 0}
          onLocationSelect={handleLocationSwitch}
          onClose={() => setIsMapOpen(false)}
        />
      )}
      {isGuildOpen && <GuildPanel characterId={characterId || 0} onClose={() => setIsGuildOpen(false)} />}
      {isBoardOpen && <BulletinBoard characterId={characterId || 0} locationId={currentLocationId} onClose={() => setIsBoardOpen(false)} />}
      {isBountyBoardOpen && <BountyBoard isOpen={isBountyBoardOpen} characterId={characterId || 0} onClose={() => setIsBountyBoardOpen(false)} />}
      {isJournalOpen && <ArtifactJournal characterId={characterId || 0} onClose={() => setIsJournalOpen(false)} />}
      <WebSocketSync clientId={clientId} characterId={characterId} onOpenMinigame={onOpenMinigame} loadState={() => loadState()} />
      <StateUpdateHandler />
      
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

        <div className="flex items-center gap-2">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleImportSave} 
            className="hidden" 
            accept=".db,.json" 
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-600/40 rounded transition-all flex items-center gap-1"
            title="Import Save State"
          >
            📂 Import
          </button>
          <button
            onClick={handleExportSave}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-emerald-600/40 rounded transition-all flex items-center gap-1"
            title="Export Save State"
          >
            💾 Export
          </button>
          <button
            onClick={() => setShowHistory(true)}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-amber-400 border border-amber-600/40 rounded transition-all flex items-center gap-1"
            title="View World History"
          >
            📜 History
          </button>
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
          <button
            onClick={() => setIsBoardOpen(true)}
            className="px-4 py-1.5 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded shadow-lg transition-all flex items-center gap-2"
          >
            <span>📜</span>
            <span>BOARD</span>
          </button>
          <button
            onClick={() => setIsGuildOpen(true)}
            className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded shadow-lg transition-all flex items-center gap-2"
          >
            <span>🛡️</span>
            <span>GUILD</span>
          </button>
          <button
            onClick={() => setIsBountyBoardOpen(true)}
            className="px-4 py-1.5 bg-red-800 hover:bg-red-700 text-white font-bold rounded shadow-lg transition-all flex items-center gap-2"
          >
            <span>⚔️</span>
            <span>BOUNTIES</span>
          </button>
          <button
            onClick={() => setIsJournalOpen(true)}
            className="px-4 py-1.5 bg-purple-700 hover:bg-purple-600 text-white font-bold rounded shadow-lg transition-all flex items-center gap-2"
          >
            <span>✨</span>
            <span>JOURNAL</span>
          </button>
          <button
            onClick={() => setIsMapOpen(true)}
            className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold rounded shadow-lg transition-all flex items-center gap-2"
          >
            <span>🧭</span>
            <span>MAP</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Side: Interactive Narration Stream */}
        <div className="flex-1 flex flex-col p-4 overflow-hidden border-r border-slate-800">
          <CombatUI worldState={worldStateData?.state} />
          <NarrativeStream
            messages={messages}
            isLoading={isLoading}
            glossary={glossaryData || null}
            onOpenCombat={onOpenCombat}
            onOpenMinigame={onOpenMinigame}
          />
          <ActionBar
            input={input}
            setInput={setInput}
            selectedMood={selectedMood}
            setSelectedMood={setSelectedMood}
            isExploration={isExploration}
            setIsExploration={setIsExploration}
            isLoading={isLoading}
            isMinigameActive={isMinigameActive}
            isMyTurn={isMyTurn}
            isCombat={!!worldStateData?.state?.is_combat_active}
            currentTurnActor={currentTurnActor}
            onSubmit={(val) => submitAction(val, false)}
          />
        </div>

        {/* Right Side: Active NPCs */}
        {isEnvExpanded ? (
          <aside className="w-full md:w-80 bg-slate-900/40 p-4 border-t md:border-t-0 md:border-l border-slate-800 flex flex-col gap-4 overflow-y-auto relative transition-all">
            <button 
              onClick={() => {
                setIsEnvExpanded(false);
                localStorage.setItem('saos_env_expanded', 'false');
              }} 
              className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center text-slate-400 hover:text-amber-500 hover:bg-slate-800 rounded transition-colors"
              title="Collapse Environment Pane"
            >
              ✕
            </button>
            <div className="bg-slate-900/80 border border-amber-900/40 p-4 rounded-xl shadow-md pr-8">
              <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>Environment Overview</span>
                <span>🧭</span>
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {currentLocation ? currentLocation.description : 'Select a location to explore.'}
              </p>
              {currentLocation?.lore_text && (
                <div className="mt-3 pt-3 border-t border-amber-900/30">
                  <details className="text-xs text-amber-200/80 group">
                    <summary className="cursor-pointer font-bold text-amber-500 hover:text-amber-400 transition-colors list-none flex items-center gap-1">
                      <span>📖</span> Read Area Lore
                    </summary>
                    <p className="mt-2 italic leading-relaxed pl-1 border-l-2 border-amber-800/50">
                      {currentLocation.lore_text}
                    </p>
                  </details>
                </div>
              )}
            </div>

            {activeNpcs.length > 0 && (
              <div className="flex-1 flex flex-col gap-3">
                <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center justify-between">
                  <span>Active NPCs ({activeNpcs.length})</span>
                  <span>👥</span>
                </h3>

                {activeNpcs.some((n) => n.in_earshot) && (
                  <div className="text-[10px] font-bold uppercase tracking-wider text-amber-500/90 flex items-center gap-1">
                    <span>🔊</span> In earshot — actively engaged
                  </div>
                )}
                {activeNpcs.filter((n) => n.in_earshot).map((npc) => renderNpcCard(npc, true))}

                {activeNpcs.some((n) => !n.in_earshot) && (
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1 mt-1">
                    <span>👤</span> Nearby
                  </div>
                )}
                {activeNpcs.filter((n) => !n.in_earshot).map((npc) => renderNpcCard(npc, false))}
              </div>
            )}
          </aside>
        ) : (
          <div className="hidden md:flex flex-col items-center justify-center p-2 border-l border-slate-800 bg-slate-900/20">
            <button 
              onClick={() => {
                setIsEnvExpanded(true);
                localStorage.setItem('saos_env_expanded', 'true');
              }}
              className="[writing-mode:vertical-rl] flex items-center gap-2 text-slate-500 hover:text-amber-500 transition-colors uppercase tracking-widest text-xs font-bold"
            >
              <span>🧭</span>
              <span>Open Environment</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

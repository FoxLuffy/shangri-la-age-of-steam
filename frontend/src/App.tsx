import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import CharacterCreation from './components/CharacterCreation';
import StatsPanel from './components/StatsPanel';
import MinigamePanel from './components/MinigamePanel';
import CombatUI from './components/CombatUI';
import EmpireUI from './components/EmpireUI';
import { fetchCharacter } from './api';
import type { Character } from './api';

import SettingsMenu from './components/SettingsMenu';

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: Error | null}> {
  constructor(props: {children: React.ReactNode}) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, errorInfo: any) {
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return <div className="p-8 text-red-500 bg-slate-950 h-screen font-mono"><h1 className="text-2xl mb-4">Frontend Crash</h1><pre>{this.state.error?.stack}</pre></div>;
    }
    return this.props.children;
  }
}

function MainApp() {
  const [characterId, setCharacterId] = useState<number | null>(() => {
    const saved = localStorage.getItem('saos_char_id');
    return saved ? parseInt(saved, 10) : null;
  });
  const [character, setCharacter] = useState<Character | null>(null);
  const [worldState, setWorldState] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [showCombat, setShowCombat] = useState(false);
  const [showMinigame, setShowMinigame] = useState(false);
  const [showEmpire, setShowEmpire] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (characterId) {
      setLoading(true);
      fetchCharacter(characterId)
        .then(char => {
          setCharacter(char);
          localStorage.setItem('saos_char_id', char.id.toString());
        })
        .catch(err => {
          console.error(err);
          setCharacterId(null);
          localStorage.removeItem('saos_char_id');
        })
        .finally(() => setLoading(false));
    }
  }, [characterId]);

  if (loading) {
    return <div className="w-full h-screen bg-slate-950 text-amber-500 flex items-center justify-center font-mono">Loading...</div>;
  }

  if (!characterId || !character) {
    return <CharacterCreation onComplete={setCharacterId} />;
  }

  const handleRetireCharacter = () => {
    if (confirm("Are you sure you want to retire this character? This will allow you to create a new one.")) {
      setCharacterId(null);
      setCharacter(null);
      setWorldState(null);
      localStorage.removeItem('saos_char_id');
    }
  };

  const activeMinigame = worldState?.active_minigame;

  return (
    <div className="w-full h-screen bg-slate-950 flex overflow-hidden relative">
      <div className="flex-1 flex flex-col p-2 sm:p-4 h-full relative">
        {showCombat && <CombatUI worldState={worldState} character={character} />}
        {showEmpire && <EmpireUI worldState={worldState} character={character} onClose={() => setShowEmpire(false)} />}
        {showSettings && <SettingsMenu character={character} onClose={() => setShowSettings(false)} onUpdateCharacter={setCharacter} />}
        <ChatInterface 
          onStateUpdate={setWorldState} 
          onOpenCombat={() => setShowCombat(true)}
          onOpenMinigame={() => setShowMinigame(true)}
        />
        {showMinigame && activeMinigame && (
          <MinigamePanel 
            minigame={activeMinigame} 
            character={character}
            onComplete={(message: string) => {
              setShowMinigame(false);
              setWorldState({ ...worldState, active_minigame: null });
              if (message) {
                window.dispatchEvent(new CustomEvent('saos_system_action', { detail: `Minigame resolution: ${message}` }));
              }
            }} 
          />
        )}
      </div>
      <StatsPanel 
        character={character} 
        worldState={worldState} 
        onReset={handleRetireCharacter} 
        onOpenEmpire={() => setShowEmpire(true)} 
        onOpenSettings={() => setShowSettings(true)}
      />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <MainApp />
    </ErrorBoundary>
  );
}

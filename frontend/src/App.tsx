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
import MarketUI from './components/MarketUI';
import AccountManager from './components/AccountManager';
import AdminPanel from './components/AdminPanel';
import SessionLobby from './components/SessionLobby';
import ReportModal from './components/ReportModal';
import { WorkshopBrowser } from './components/WorkshopBrowser';

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
  const [authToken, setAuthToken] = useState<string | null>(() => localStorage.getItem('saos_auth_token'));
  const [userId, setUserId] = useState<number | null>(() => {
    const saved = localStorage.getItem('saos_user_id');
    return saved ? parseInt(saved, 10) : null;
  });
  const [isAdmin, setIsAdmin] = useState<boolean>(() => localStorage.getItem('saos_is_admin') === 'true');

  const [characterId, setCharacterId] = useState<number | null>(() => {
    const saved = localStorage.getItem('saos_char_id');
    return saved ? parseInt(saved, 10) : null;
  });
  const [sessionInfo, setSessionInfo] = useState<any>(() => {
    const saved = localStorage.getItem('saos_session_info');
    return saved ? JSON.parse(saved) : null;
  });
  const [character, setCharacter] = useState<Character | null>(null);
  const [worldState, setWorldState] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [showCombat, setShowCombat] = useState(false);
  const [showMinigame, setShowMinigame] = useState(false);
  const [showEmpire, setShowEmpire] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showMarket, setShowMarket] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showWorkshop, setShowWorkshop] = useState(false);

  useEffect(() => {
    if (characterId) {
      setLoading(true);
      fetchCharacter(characterId)
        .then(char => {
          // If the character belongs to another user, we might want to handle it, but for now we just load it
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

  const handleLogin = (token: string, uId: number, adminStatus: boolean) => {
    setAuthToken(token);
    setUserId(uId);
    setIsAdmin(adminStatus);
    localStorage.setItem('saos_auth_token', token);
    localStorage.setItem('saos_user_id', uId.toString());
    localStorage.setItem('saos_is_admin', adminStatus.toString());
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUserId(null);
    setIsAdmin(false);
    setCharacterId(null);
    setCharacter(null);
    setWorldState(null);
    setSessionInfo(null);
    localStorage.removeItem('saos_auth_token');
    localStorage.removeItem('saos_user_id');
    localStorage.removeItem('saos_is_admin');
    localStorage.removeItem('saos_char_id');
    localStorage.removeItem('saos_session_info');
  };

  if (!authToken) {
    return <AccountManager onLogin={handleLogin} />;
  }

  if (!sessionInfo) {
    return (
      <div className="w-full h-screen bg-slate-950 flex flex-col relative overflow-hidden">
        <div className="absolute top-4 right-4 z-50 flex gap-2">
          {isAdmin && (
            <button onClick={() => setShowAdmin(true)} className="bg-purple-900/50 hover:bg-purple-900 text-purple-200 px-4 py-2 border border-purple-900 rounded">
              Admin Panel
            </button>
          )}
          <button onClick={() => setShowReportModal(true)} className="bg-orange-900/50 hover:bg-orange-900 text-orange-200 px-4 py-2 border border-orange-900 rounded">
            Report
          </button>
          <button onClick={handleLogout} className="bg-red-900/50 hover:bg-red-900 text-red-200 px-4 py-2 border border-red-900 rounded">
            Logout
          </button>
        </div>
        {showAdmin && authToken && <AdminPanel token={authToken} onClose={() => setShowAdmin(false)} />}
        {showReportModal && <ReportModal userId={userId} onClose={() => setShowReportModal(false)} />}
        <SessionLobby onSessionSelect={(mode, sId, pwd) => {
          const info = { mode, sessionId: sId, password: pwd };
          setSessionInfo(info);
          localStorage.setItem('saos_session_info', JSON.stringify(info));
        }} />
      </div>
    );
  }

  if (loading) {
    return <div className="w-full h-screen bg-slate-950 text-amber-500 flex items-center justify-center font-mono">Loading...</div>;
  }

  if (!characterId || !character) {
    return (
      <div className="w-full h-screen bg-slate-950 flex flex-col relative overflow-hidden">
        <div className="absolute top-4 right-4 z-50 flex gap-2">
          {isAdmin && (
            <button onClick={() => setShowAdmin(true)} className="bg-purple-900/50 hover:bg-purple-900 text-purple-200 px-4 py-2 border border-purple-900 rounded">
              Admin Panel
            </button>
          )}
          <button onClick={() => setShowReportModal(true)} className="bg-orange-900/50 hover:bg-orange-900 text-orange-200 px-4 py-2 border border-orange-900 rounded">
            Report
          </button>
          <button onClick={handleLogout} className="bg-red-900/50 hover:bg-red-900 text-red-200 px-4 py-2 border border-red-900 rounded">
            Logout
          </button>
        </div>
        {showAdmin && authToken && <AdminPanel token={authToken} onClose={() => setShowAdmin(false)} />}
        {showReportModal && <ReportModal userId={userId} onClose={() => setShowReportModal(false)} />}
        <CharacterCreation onComplete={setCharacterId} userId={userId} />
      </div>
    );
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
        <div className="absolute top-2 right-2 z-50 flex gap-2">
          {isAdmin && (
            <button onClick={() => setShowAdmin(true)} className="bg-purple-900/50 text-purple-200 px-2 py-1 text-xs border border-purple-900 rounded">
              Admin Panel
            </button>
          )}
          <button onClick={() => setShowReportModal(true)} className="bg-orange-900/50 text-orange-200 px-2 py-1 text-xs border border-orange-900 rounded">
            Report
          </button>
          <button onClick={handleLogout} className="bg-red-900/50 text-red-200 px-2 py-1 text-xs border border-red-900 rounded">
            Logout
          </button>
        </div>
        {showCombat && <CombatUI worldState={worldState} character={character} />}
        {showEmpire && <EmpireUI worldState={worldState} character={character} onClose={() => setShowEmpire(false)} />}
        {showSettings && <SettingsMenu character={character} onClose={() => setShowSettings(false)} onUpdateCharacter={setCharacter} />}
        {showMarket && <MarketUI character={character} onClose={() => setShowMarket(false)} onUpdateCharacter={setCharacter} />}
        {showAdmin && authToken && <AdminPanel token={authToken} onClose={() => setShowAdmin(false)} />}
        {showReportModal && <ReportModal userId={userId} onClose={() => setShowReportModal(false)} />}
        {showWorkshop && (
          <div className="absolute inset-0 z-40 bg-slate-950/80 p-4 sm:p-12 flex flex-col items-center">
             <div className="w-full max-w-4xl relative">
                <button onClick={() => setShowWorkshop(false)} className="absolute top-2 right-2 text-white bg-red-600 px-3 py-1 rounded">Close</button>
                <WorkshopBrowser />
             </div>
          </div>
        )}
        <ChatInterface 
          characterId={character.id}
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
        onOpenMarket={() => setShowMarket(true)} 
        onOpenSettings={() => setShowSettings(true)}
        onOpenWorkshop={() => setShowWorkshop(true)}
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

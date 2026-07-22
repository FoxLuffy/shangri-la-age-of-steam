import { useState } from 'react';

interface SessionLobbyProps {
  onSessionSelect: (mode: string, sessionId?: string, password?: string) => void;
}

export default function SessionLobby({ onSessionSelect }: SessionLobbyProps) {
  const [activeTab, setActiveTab] = useState<'solo' | 'host' | 'join_public' | 'join_private'>('solo');
  const [sessionId, setSessionId] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 font-mono text-amber-500 w-full p-4">
      <div className="bg-slate-900 p-8 rounded-lg border border-amber-900/50 shadow-2xl max-w-2xl w-full">
        <h2 className="text-3xl font-bold text-center mb-8 text-amber-400">
          UPLINK ESTABLISHED: SELECT PROTOCOL
        </h2>

        <div className="grid grid-cols-4 gap-2 mb-8 border-b border-amber-900/50 pb-4">
          <button 
            className={`py-3 text-sm rounded transition-colors ${activeTab === 'solo' ? 'bg-amber-600 text-slate-950 font-bold' : 'bg-slate-800 hover:bg-slate-700'}`}
            onClick={() => setActiveTab('solo')}
          >
            Solo Protocol
          </button>
          <button 
            className={`py-3 text-sm rounded transition-colors ${activeTab === 'host' ? 'bg-amber-600 text-slate-950 font-bold' : 'bg-slate-800 hover:bg-slate-700'}`}
            onClick={() => setActiveTab('host')}
          >
            Host Co-Op
          </button>
          <button 
            className={`py-3 text-sm rounded transition-colors ${activeTab === 'join_public' ? 'bg-amber-600 text-slate-950 font-bold' : 'bg-slate-800 hover:bg-slate-700'}`}
            onClick={() => setActiveTab('join_public')}
          >
            Public Lobbies
          </button>
          <button 
            className={`py-3 text-sm rounded transition-colors ${activeTab === 'join_private' ? 'bg-amber-600 text-slate-950 font-bold' : 'bg-slate-800 hover:bg-slate-700'}`}
            onClick={() => setActiveTab('join_private')}
          >
            Join Private
          </button>
        </div>

        <div className="min-h-[200px] flex flex-col justify-center">
          {activeTab === 'solo' && (
            <div className="text-center space-y-4">
              <p className="text-amber-200">Engage the world alone. Your local instance will sync to the global asynchronous market and ledger.</p>
              <button 
                onClick={() => onSessionSelect('solo')}
                className="bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-3 px-8 rounded mt-4"
              >
                Commence Solo Journey
              </button>
            </div>
          )}

          {activeTab === 'host' && (
            <div className="space-y-4 max-w-md mx-auto w-full">
              <p className="text-center text-amber-200 mb-4">Host a synchronous multiplayer session. Max 4 Operatives.</p>
              <div>
                <label className="block text-sm mb-1 text-amber-600">Session Password (Optional)</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Leave blank for public"
                  className="w-full bg-slate-950 border border-amber-900 rounded p-2 text-amber-100"
                />
              </div>
              <button 
                onClick={() => onSessionSelect('host', undefined, password)}
                className="w-full bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-3 px-4 rounded mt-4"
              >
                Initialize Host Node
              </button>
            </div>
          )}

          {activeTab === 'join_public' && (
            <div className="text-center space-y-4">
              <p className="text-amber-200 mb-4">Searching local subnet for public sessions...</p>
              <div className="border border-amber-900/30 rounded p-4 bg-slate-950/50">
                <p className="text-slate-500 italic">No public sessions detected in your sector.</p>
              </div>
              <button 
                onClick={() => alert("Searching network... no sessions found.")}
                className="bg-slate-700 hover:bg-slate-600 text-amber-200 font-bold py-2 px-6 rounded mt-4"
              >
                Refresh Scan
              </button>
            </div>
          )}

          {activeTab === 'join_private' && (
            <div className="space-y-4 max-w-md mx-auto w-full">
              <p className="text-center text-amber-200 mb-4">Connect to an encrypted session via ID and password.</p>
              <div>
                <label className="block text-sm mb-1 text-amber-600">Session ID</label>
                <input
                  type="text"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  className="w-full bg-slate-950 border border-amber-900 rounded p-2 text-amber-100 mb-4"
                />
              </div>
              <div>
                <label className="block text-sm mb-1 text-amber-600">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-amber-900 rounded p-2 text-amber-100"
                />
              </div>
              <button 
                onClick={() => onSessionSelect('join_private', sessionId, password)}
                disabled={!sessionId}
                className="w-full bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-3 px-4 rounded mt-4 disabled:opacity-50"
              >
                Authenticate & Join
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

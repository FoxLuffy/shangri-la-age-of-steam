import { useState } from 'react';
import axios from 'axios';
import { BACKEND_URL } from '../api';

export default function MinigamePanel({ minigame, onComplete }: { minigame: any, onComplete: () => void }) {
  const [state, setState] = useState(minigame.state);
  const [loading, setLoading] = useState(false);

  const handlePlay = async (action: string, data: any = {}) => {
    try {
      setLoading(true);
      const res = await axios.post(`${BACKEND_URL}/minigame/play`, {
        minigame_id: minigame.id,
        action,
        data
      });
      setState(res.data.state);
      if (res.data.solved) {
        setTimeout(() => {
          onComplete();
        }, 2000);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderHackGame = () => {
    return (
      <div className="flex flex-col gap-4 items-center">
        <div className="text-sm font-mono text-cyan-400 border border-cyan-800 bg-cyan-950/50 p-2 text-center w-full">
          {state.message}
        </div>
        
        <div className="flex gap-2">
          {['A', 'B', 'C'].map((char) => (
            <button
              key={char}
              disabled={loading}
              onClick={() => handlePlay('input', { value: char })}
              className="w-12 h-12 flex items-center justify-center border border-slate-600 bg-slate-800 hover:bg-slate-700 text-amber-500 font-mono text-xl"
            >
              {char}
            </button>
          ))}
        </div>
        
        <div className="text-xs text-slate-400 font-mono">
          Current Input: {state.current_input?.join(' ') || 'none'}
        </div>
        <div className="text-xs text-rose-400 font-mono">
          Attempts Left: {state.attempts_left}
        </div>
      </div>
    );
  };

  const renderLockpickGame = () => {
    return (
      <div className="flex flex-col gap-4 items-center">
        <div className="text-sm font-mono text-amber-400 border border-amber-800 bg-amber-950/50 p-2 text-center w-full">
          {state.message}
        </div>
        
        <div className="flex gap-4">
          {state.pins?.map((isSet: boolean, idx: number) => (
            <div key={idx} className="flex flex-col gap-2 items-center">
              <div className={`w-8 h-16 border border-slate-600 rounded-t-full transition-all ${isSet ? 'bg-emerald-600' : 'bg-slate-800'}`}></div>
              <button
                disabled={isSet || loading}
                onClick={() => handlePlay('set_pin', { pin_index: idx })}
                className="px-2 py-1 bg-amber-900/50 hover:bg-amber-800 text-amber-200 text-xs font-mono uppercase border border-amber-700/50"
              >
                Pick
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
      <div className="w-[400px] border border-amber-900/50 bg-slate-900 p-6 shadow-2xl relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-rose-500"></div>
        <h2 className="text-xl font-serif text-amber-500 mb-4 uppercase tracking-widest text-center">
          {minigame.type === 'hack' ? 'Terminal Override' : 'Lockpicking'}
        </h2>
        
        <div className="min-h-[200px] flex items-center justify-center">
          {minigame.type === 'hack' && renderHackGame()}
          {minigame.type === 'lockpick' && renderLockpickGame()}
        </div>
        
        <div className="mt-6 flex justify-center">
          <button 
            disabled={loading}
            onClick={() => handlePlay('abandon')}
            className="text-xs font-mono text-slate-500 hover:text-rose-400 uppercase tracking-widest"
          >
            Abandon Attempt
          </button>
        </div>
      </div>
    </div>
  );
}

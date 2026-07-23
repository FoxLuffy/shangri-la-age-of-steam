import { useState } from 'react';
import axios from 'axios';
import { BACKEND_URL } from '../api';
import TutorialBox from './TutorialBox';
import type { Character } from '../api';

export default function MinigamePanel({ minigame, character, onComplete }: { minigame: any, character: Character, onComplete: (message: string) => void }) {
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
          onComplete(res.data.state.message);
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
      <div className="flex flex-col gap-4 items-center w-full">
        <div className="text-sm font-mono text-cyan-400 border border-cyan-800 bg-cyan-950/50 p-2 text-center w-full">
          {state.message}
        </div>

        {/* Guesses history */}
        <div className="flex flex-col gap-1 w-full max-h-40 overflow-y-auto pr-2">
          {state.guesses?.map((g: any, i: number) => (
            <div key={i} className="flex justify-between items-center bg-slate-800/50 p-1 border border-slate-700">
              <div className="flex gap-1 font-mono text-cyan-200">
                {g.guess.map((char: string, idx: number) => (
                  <span key={idx} className="w-6 h-6 flex items-center justify-center bg-slate-900 border border-slate-600">{char}</span>
                ))}
              </div>
              <div className="flex gap-2 text-xs">
                <span className="text-emerald-400" title="Correct Position">Exact: {g.correct_pos}</span>
                <span className="text-amber-400" title="Correct Character">Present: {g.correct_char}</span>
              </div>
            </div>
          ))}
        </div>
        
        <div className="flex gap-2 mt-2">
          {['A', 'B', 'C', 'D', 'E', 'F'].map((char) => (
            <button
              key={char}
              disabled={loading || (state.current_input && state.sequence && state.current_input.length >= state.sequence.length)}
              onClick={() => handlePlay('input', { value: char })}
              className="w-10 h-10 flex items-center justify-center border border-slate-600 bg-slate-800 hover:bg-slate-700 text-amber-500 font-mono text-xl"
            >
              {char}
            </button>
          ))}
        </div>
        
        <div className="flex justify-between w-full mt-2">
          <div className="text-xs text-slate-400 font-mono flex items-center gap-1">
            Input: 
            <div className="flex gap-1">
              {Array.from({ length: state.sequence?.length || 4 }).map((_, i) => (
                <span key={i} className="w-6 h-6 flex items-center justify-center bg-slate-900 border border-slate-700 text-cyan-300">
                  {state.current_input?.[i] || ''}
                </span>
              ))}
            </div>
          </div>
          <div className="text-xs text-rose-400 font-mono flex items-center">
            Attempts: {state.attempts_left}
          </div>
        </div>
        <div className="w-full flex justify-end">
             <button
                disabled={loading || !state.current_input || state.current_input.length === 0}
                onClick={() => handlePlay('clear_input')}
                className="text-xs font-mono text-slate-400 hover:text-slate-200 uppercase tracking-widest px-2 py-1 bg-slate-800 border border-slate-700"
              >
                Clear Input
              </button>
        </div>
      </div>
    );
  };

  const renderLockpickGame = () => {
    return (
      <div className="flex flex-col gap-4 items-center">
        <div className="flex flex-col gap-2 w-full text-center">
          <div className="text-sm font-mono text-amber-400 border border-amber-800 bg-amber-950/50 p-2">
            {state.message}
          </div>
          <div className="text-xs text-amber-500/70 italic font-serif">
            Click 'Pick' to align each pin tumbler. Align all pins to open the lock.
          </div>
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
      <div className="w-[400px] border border-amber-900/50 bg-slate-900 p-6 shadow-2xl relative flex flex-col gap-4">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-rose-500"></div>
        <h2 className="text-xl font-serif text-amber-500 uppercase tracking-widest text-center">
          {minigame.type === 'hack' ? 'Terminal Override' : 'Lockpicking'}
        </h2>

        {state.hint && !state.hint_revealed && (
          <button
            onClick={() => handlePlay('reveal_hint')}
            disabled={loading}
            className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center border border-amber-500 bg-amber-900/50 hover:bg-amber-800 text-amber-300 rounded-full animate-pulse transition-all shadow-[0_0_10px_rgba(245,158,11,0.5)]"
            title="Crack open a Hint Gear"
          >
            ⚙️
          </button>
        )}
        
        <TutorialBox 
          title="Minigame Mechanics" 
          message={minigame.type === 'hack' ? "Guess the correct character sequence to bypass the terminal. The narrator might offer hints in the narrative!" : "Carefully align the tumblers. Remember that rushing might break your pick."}
          isEnabled={character.show_tutorials} 
        />

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

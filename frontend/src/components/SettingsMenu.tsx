import { useState } from 'react';
import { toggleTutorials } from '../api';
import type { Character } from '../api';

export default function SettingsMenu({ character, onClose, onUpdateCharacter }: { character: Character, onClose: () => void, onUpdateCharacter: (char: Character) => void }) {
  const [showTutorials, setShowTutorials] = useState(character.show_tutorials);
  const [loading, setLoading] = useState(false);

  const handleToggle = async () => {
    setLoading(true);
    try {
      const result = await toggleTutorials(character.id, !showTutorials);
      setShowTutorials(result.show_tutorials);
      onUpdateCharacter({ ...character, show_tutorials: result.show_tutorials });
    } catch (e) {
      console.error(e);
      alert('Failed to update settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-8 font-mono">
      <div className="bg-slate-900 border-2 border-amber-900/50 shadow-2xl shadow-amber-900/20 max-w-md w-full flex flex-col">
        <div className="p-4 border-b border-amber-900/30 bg-slate-800/50 flex justify-between items-center">
          <h2 className="text-xl text-amber-500 uppercase tracking-widest font-serif">Settings</h2>
          <button onClick={onClose} className="text-amber-500 hover:text-amber-300 text-2xl px-2">✕</button>
        </div>
        
        <div className="p-6 space-y-6 text-amber-100">
          <div className="flex items-center justify-between p-4 border border-amber-900/30 bg-slate-800/30">
            <div>
              <div className="text-sm uppercase text-amber-400">Interactive Tutorials</div>
              <div className="text-xs text-amber-600/70 mt-1">Show tutorial overlays on new screens like Combat, Empire, and Minigames.</div>
            </div>
            <button 
              onClick={handleToggle}
              disabled={loading}
              className={`px-4 py-2 text-xs uppercase tracking-wider border ${showTutorials ? 'bg-amber-900/40 border-amber-500 text-amber-400' : 'bg-slate-800 border-slate-600 text-slate-400'}`}
            >
              {loading ? '...' : showTutorials ? 'Enabled' : 'Disabled'}
            </button>
          </div>

          <div className="flex flex-col gap-3 p-4 border border-amber-900/30 bg-slate-800/30">
            <div>
              <div className="text-sm uppercase text-amber-400">Narrator Speed</div>
              <div className="text-xs text-amber-600/70 mt-1">Adjust how fast the narrator's text streams into the log.</div>
            </div>
            <div className="flex gap-2">
              {['Fast', 'Normal', 'Slow'].map(speed => (
                <button
                  key={speed}
                  onClick={() => {
                    localStorage.setItem('saos_narrator_speed', speed);
                    setLoading(true); setTimeout(() => setLoading(false), 50);
                  }}
                  className={`flex-1 py-2 text-xs uppercase tracking-wider border ${
                    (localStorage.getItem('saos_narrator_speed') || 'Fast') === speed
                      ? 'bg-amber-900/40 border-amber-500 text-amber-400 font-bold'
                      : 'bg-slate-800 border-slate-600 text-slate-400 hover:bg-slate-700'
                  }`}
                >
                  {speed}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between p-4 border border-amber-900/30 bg-slate-800/30">
            <div>
              <div className="text-sm uppercase text-amber-400">Audio</div>
              <div className="text-xs text-amber-600/70 mt-1">Enable ambient background noises and procedural music.</div>
            </div>
            <button 
              onClick={() => {
                const current = localStorage.getItem('saos_audio_enabled') !== 'false';
                localStorage.setItem('saos_audio_enabled', current ? 'false' : 'true');
                setLoading(true); setTimeout(() => setLoading(false), 50);
              }}
              disabled={loading}
              className={`px-4 py-2 text-xs uppercase tracking-wider border ${
                localStorage.getItem('saos_audio_enabled') !== 'false' 
                  ? 'bg-amber-900/40 border-amber-500 text-amber-400' 
                  : 'bg-slate-800 border-slate-600 text-slate-400'
              }`}
            >
              {localStorage.getItem('saos_audio_enabled') !== 'false' ? 'Enabled' : 'Disabled'}
            </button>
          </div>

          <div className="flex items-center justify-between p-4 border border-amber-900/30 bg-slate-800/30">
            <div>
              <div className="text-sm uppercase text-amber-400">Auto-expand Environment</div>
              <div className="text-xs text-amber-600/70 mt-1">Automatically open the Environment pane when NPCs or location changes.</div>
            </div>
            <button 
              onClick={() => {
                const current = localStorage.getItem('saos_auto_expand_env') === 'true';
                localStorage.setItem('saos_auto_expand_env', current ? 'false' : 'true');
                setLoading(true); setTimeout(() => setLoading(false), 50);
              }}
              disabled={loading}
              className={`px-4 py-2 text-xs uppercase tracking-wider border ${
                localStorage.getItem('saos_auto_expand_env') === 'true' 
                  ? 'bg-amber-900/40 border-amber-500 text-amber-400' 
                  : 'bg-slate-800 border-slate-600 text-slate-400'
              }`}
            >
              {localStorage.getItem('saos_auto_expand_env') === 'true' ? 'Enabled' : 'Disabled'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

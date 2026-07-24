import { type FormEvent } from 'react';

interface ActionBarProps {
  input: string;
  setInput: (val: string) => void;
  selectedMood: string;
  setSelectedMood: (val: string) => void;
  isExploration: boolean;
  setIsExploration: (val: boolean) => void;
  isLoading: boolean;
  isMinigameActive: boolean;
  isMyTurn: boolean;
  currentTurnActor: string;
  onSubmit: (actionText: string) => void;
}

export default function ActionBar({
  input,
  setInput,
  selectedMood,
  setSelectedMood,
  isExploration,
  setIsExploration,
  isLoading,
  isMinigameActive,
  isMyTurn,
  currentTurnActor,
  onSubmit
}: ActionBarProps) {
  const moods = [
    { id: '', label: 'Neutral 😐' },
    { id: 'cautious', label: 'Cautious 🔍' },
    { id: 'bold', label: 'Bold ⚔️' },
    { id: 'inquisitive', label: 'Inquisitive 📜' },
    { id: 'tense', label: 'Tense ⚡' }
  ];

  const handleSendMessage = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input.trim());
    }
  };

  return (
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
          placeholder={isMinigameActive ? "Focus on the minigame..." : !isMyTurn ? `Waiting for ${currentTurnActor} to act...` : "Type your action (e.g., 'Inspect the copper pressure gauge' or 'Talk to Barnaby')..."}
          className="flex-1 bg-slate-900 border border-amber-800/50 rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-amber-500 text-amber-100 placeholder-slate-500 shadow-inner disabled:opacity-50"
          disabled={isLoading || isMinigameActive || !isMyTurn}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim() || isMinigameActive || !isMyTurn}
          className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-slate-950 font-bold px-6 py-3 rounded-lg text-sm transition-all shadow-lg flex items-center gap-2"
        >
          <span>SEND</span>
          <span>➔</span>
        </button>
      </div>
    </form>
  );
}

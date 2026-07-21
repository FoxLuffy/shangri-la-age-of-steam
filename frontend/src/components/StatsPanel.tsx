import type { Character } from '../api';

export default function StatsPanel({ character, worldState, onReset }: { character: Character, worldState?: any, onReset: () => void }) {
  return (
    <div className="w-64 bg-slate-900 border-l border-amber-900/30 flex flex-col p-4 overflow-y-auto">
      <div className="text-xs font-mono text-amber-600/70 uppercase tracking-widest mb-4 border-b border-amber-900/30 pb-2">
        Dossier
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-serif text-amber-500 mb-1">{character.name}</h2>
        <div className="text-sm text-amber-400 font-mono uppercase">{character.character_class}</div>
      </div>

      <div className="mb-6">
        <div className="text-xs text-amber-600/70 uppercase mb-2">Stats</div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm font-mono text-amber-200">
            <span>Strength</span>
            <span className="text-amber-500">{character.stats.strength}</span>
          </div>
          <div className="flex justify-between text-sm font-mono text-amber-200">
            <span>Intellect</span>
            <span className="text-amber-500">{character.stats.intellect}</span>
          </div>
          <div className="flex justify-between text-sm font-mono text-amber-200">
            <span>Charm</span>
            <span className="text-amber-500">{character.stats.charm}</span>
          </div>
        </div>
      </div>

      <div className="mb-6 flex-1">
        <div className="text-xs text-amber-600/70 uppercase mb-2">Backstory</div>
        <p className="text-sm font-serif text-amber-100/70 italic leading-relaxed">
          "{character.background}"
        </p>
      </div>

      {worldState && worldState.inventory && worldState.inventory.length > 0 && (
        <div className="mb-6">
          <div className="text-xs text-amber-600/70 uppercase mb-2">Inventory</div>
          <div className="space-y-2">
            {worldState.inventory.map((item: any, i: number) => (
              <div key={i} className="flex justify-between items-start text-sm">
                <span className="text-amber-200 font-mono" title={item.description}>{item.name}</span>
                <span className="text-amber-500 font-mono text-xs ml-2">x{item.quantity}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {worldState && worldState.quests && worldState.quests.length > 0 && (
        <div className="mb-6">
          <div className="text-xs text-amber-600/70 uppercase mb-2">Quests</div>
          <div className="space-y-3">
            {worldState.quests.map((quest: any, i: number) => (
              <div key={i} className="text-sm border-l-2 border-amber-900/40 pl-2">
                <div className="font-serif text-amber-400 mb-1 flex justify-between">
                  <span>{quest.title}</span>
                  <span className={`text-[10px] uppercase tracking-wider ${
                    quest.state === 'Completed' ? 'text-emerald-400' :
                    quest.state === 'Failed' ? 'text-rose-400' : 'text-sky-400'
                  }`}>
                    [{quest.state}]
                  </span>
                </div>
                <div className="text-xs text-amber-100/60 leading-tight">
                  {quest.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-auto pt-4 border-t border-amber-900/30">
        <button
          onClick={onReset}
          className="w-full px-3 py-2 text-xs bg-slate-800 hover:bg-rose-900/40 text-rose-400/80 hover:text-rose-400 border border-slate-700 hover:border-rose-800/40 rounded transition-all flex items-center justify-center gap-2 uppercase tracking-wider"
          title="Delete Character and Start Over"
        >
          <span>⚰️</span> Retire Character
        </button>
      </div>
    </div>
  );
}

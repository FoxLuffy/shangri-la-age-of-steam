import type { Character } from '../api';

export default function StatsPanel({ character, worldState, onReset, onOpenEmpire }: { character: Character, worldState?: any, onReset: () => void, onOpenEmpire?: () => void }) {
  return (
    <div className="w-64 bg-slate-900 border-l border-amber-900/30 flex flex-col p-4 overflow-y-auto">
      <div className="text-xs font-mono text-amber-600/70 uppercase tracking-widest mb-4 border-b border-amber-900/30 pb-2">
        Dossier
      </div>

      <div className="mb-4">
        <h2 className="text-xl font-serif text-amber-500 mb-1">{character.name}</h2>
        <div className="text-sm text-amber-400 font-mono uppercase">{character.character_class}</div>
      </div>

      {worldState && (
        <div className="mb-6 p-2 bg-slate-800/50 border border-amber-900/30 rounded flex justify-between items-center cursor-pointer hover:bg-slate-800 transition-colors" onClick={onOpenEmpire}>
          <div>
            <div className="text-[10px] text-amber-600/70 uppercase font-mono">Wealth</div>
            <div className="text-sm font-mono text-amber-400">{worldState.brass_coins || 0} Coins</div>
          </div>
          <button className="text-xs px-2 py-1 bg-amber-900/40 text-amber-500 rounded border border-amber-900 hover:bg-amber-800/60 uppercase tracking-wider">
            Empire
          </button>
        </div>
      )}

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

      {worldState && worldState.factions && worldState.factions.length > 0 && (
        <div className="mb-6">
          <div className="text-xs text-amber-600/70 uppercase mb-2">Factions</div>
          <div className="space-y-3">
            {worldState.factions.map((faction: any, i: number) => (
              <div key={i} className="text-sm">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-serif text-amber-200">{faction.faction_name}</span>
                  <span className={`text-[10px] uppercase tracking-wider ${
                    faction.standing > 0.5 ? 'text-emerald-400' :
                    faction.standing > 0 ? 'text-emerald-200/70' :
                    faction.standing < -0.5 ? 'text-rose-500' :
                    faction.standing < 0 ? 'text-rose-300' : 'text-slate-400'
                  }`}>
                    {faction.standing > 0.5 ? 'Revered' :
                     faction.standing > 0 ? 'Friendly' :
                     faction.standing < -0.5 ? 'Hated' :
                     faction.standing < 0 ? 'Hostile' : 'Neutral'}
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded overflow-hidden relative">
                  <div className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-slate-600 z-10"></div>
                  <div 
                    className={`h-full absolute top-0 bottom-0 ${faction.standing >= 0 ? 'bg-emerald-500/70' : 'bg-rose-500/70'}`}
                    style={{ 
                      width: `${Math.abs(faction.standing) * 50}%`, 
                      left: faction.standing >= 0 ? '50%' : `${50 + (faction.standing * 50)}%` 
                    }}
                  ></div>
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

import type { Character } from '../api';

export default function StatsPanel({ character }: { character: Character }) {
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

      <div>
        <div className="text-xs text-amber-600/70 uppercase mb-2">Backstory</div>
        <p className="text-sm font-serif text-amber-100/70 italic leading-relaxed">
          "{character.background}"
        </p>
      </div>
    </div>
  );
}

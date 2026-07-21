

interface CombatUIProps {
  worldState: any;
}

export default function CombatUI({ worldState }: CombatUIProps) {
  if (!worldState || !worldState.is_combat_active) {
    return null;
  }

  const { player_stats, active_npcs } = worldState;
  
  if (!player_stats || !active_npcs) return null;

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 w-full max-w-2xl px-4 flex flex-col gap-4 pointer-events-none">
      
      {/* Enemy Health Bars */}
      <div className="flex flex-col gap-2 pointer-events-auto items-center">
        {active_npcs.filter((npc: any) => npc.hp !== undefined && npc.max_hp !== undefined).map((npc: any) => (
          <div key={npc.id} className="w-64 bg-slate-900/90 border border-red-900/50 p-2 rounded flex flex-col gap-1 backdrop-blur-sm">
            <div className="flex justify-between items-end">
              <span className="text-red-400 font-serif text-sm">{npc.name}</span>
              <span className="text-red-500/70 text-xs">{npc.hp}/{npc.max_hp}</span>
            </div>
            <div className="w-full bg-slate-950 h-2 rounded overflow-hidden">
              <div 
                className="bg-red-600 h-full transition-all duration-300"
                style={{ width: `${(npc.hp / npc.max_hp) * 100}%` }}
              ></div>
            </div>
            {npc.status_effects && npc.status_effects.length > 0 && (
              <div className="flex gap-1 mt-1 flex-wrap">
                {npc.status_effects.map((fx: string, i: number) => (
                  <span key={i} className="text-[10px] bg-red-900/30 text-red-300 px-1 rounded">{fx}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Player Combat HUD */}
      <div className="fixed bottom-24 left-1/2 -translate-x-1/2 flex gap-8 items-end pointer-events-auto z-50">
        {/* Steam Gauge */}
        <div className="flex flex-col items-center gap-1">
          <div className="h-32 w-6 bg-slate-900/90 border border-cyan-900/50 rounded-t-lg overflow-hidden relative backdrop-blur-sm flex items-end">
            <div 
              className="w-full bg-cyan-500/80 transition-all duration-300 relative shadow-[0_0_15px_rgba(6,182,212,0.6)]"
              style={{ height: `${(player_stats.steam / player_stats.max_steam) * 100}%` }}
            >
            </div>
          </div>
          <span className="text-[10px] text-cyan-500 uppercase tracking-widest font-mono bg-slate-900/80 px-1 rounded shadow-sm">Steam</span>
        </div>

        {/* Player HP */}
        <div className="flex flex-col items-center gap-1 mb-4">
          <div className="text-4xl font-serif text-emerald-400 drop-shadow-[0_0_12px_rgba(52,211,153,0.5)]">
            {player_stats.hp}
          </div>
          <span className="text-[10px] text-emerald-500/70 uppercase tracking-widest font-mono bg-slate-900/80 px-1 rounded">Vitality</span>
        </div>
      </div>
    </div>
  );
}

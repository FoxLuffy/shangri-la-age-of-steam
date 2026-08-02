import type { Character } from '../api';

interface CombatUIProps {
  worldState: any;
  character?: Character;
}

// Docked combat pane (like the minigame panel): organized enemy health bars, a turn/round
// indicator, and the player's Vitality/Steam — no more scattered floating overlays.
export default function CombatUI({ worldState }: CombatUIProps) {
  if (!worldState || !worldState.is_combat_active) {
    return null;
  }

  const { player_stats, active_npcs, combat_state } = worldState;
  if (!player_stats || !active_npcs) return null;

  const enemies = active_npcs.filter((npc: any) => npc.hp !== undefined && npc.max_hp !== undefined);
  const turnActor = combat_state?.turn_order?.[combat_state?.current_turn_index]?.name;

  const maxHp = player_stats.max_hp || 100;
  const hpPct = Math.max(0, Math.min(100, (player_stats.hp / maxHp) * 100));
  const steamPct = Math.max(0, Math.min(100, (player_stats.steam / (player_stats.max_steam || 100)) * 100));

  return (
    <div className="mb-3 bg-slate-900/95 border-2 border-red-900/60 rounded-xl p-3 shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
          <span>⚔️</span> In Combat
        </h3>
        {turnActor && <span className="text-[11px] text-red-300/80">Turn: {turnActor}</span>}
      </div>

      {/* Enemy health bars */}
      <div className="flex flex-col gap-2 mb-3">
        {enemies.length === 0 && <p className="text-xs text-slate-400">No visible opponents.</p>}
        {enemies.map((npc: any) => (
          <div key={npc.id} className="bg-slate-950/70 border border-red-900/40 p-2 rounded">
            <div className="flex justify-between items-end mb-1">
              <span className="text-red-400 font-serif text-sm">{npc.name}</span>
              <span className="text-red-500/70 text-xs">{npc.hp}/{npc.max_hp}</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded overflow-hidden">
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

      {/* Player vitals */}
      <div className="flex items-center gap-4">
        <div className="flex flex-col flex-1">
          <div className="flex justify-between text-[10px] uppercase tracking-widest mb-0.5">
            <span className="text-emerald-500/80">Vitality</span>
            <span className="text-emerald-400">{player_stats.hp}</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded overflow-hidden">
            <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${hpPct}%` }}></div>
          </div>
        </div>
        <div className="flex flex-col flex-1">
          <div className="flex justify-between text-[10px] uppercase tracking-widest mb-0.5">
            <span className="text-cyan-500/80">Steam</span>
            <span className="text-cyan-400">{player_stats.steam}</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded overflow-hidden">
            <div className="bg-cyan-500 h-full transition-all duration-300" style={{ width: `${steamPct}%` }}></div>
          </div>
        </div>
      </div>

      <p className="text-[11px] text-slate-400 mt-2 italic">Type your combat actions in the chat below — attack, use the environment, or flee.</p>
    </div>
  );
}

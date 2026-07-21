import TutorialBox from './TutorialBox';
import type { Character } from '../api';

export default function EmpireUI({ worldState, character, onClose }: { worldState: any, character: Character, onClose: () => void }) {
  if (!worldState) return null;

  const playerProperties = worldState.properties?.filter((p: any) => p.owner_id === worldState.player_stats?.id) || [];
  const localProperties = worldState.properties?.filter((p: any) => p.location_id === worldState.current_location_id) || [];
  
  const totalIncome = playerProperties.reduce((sum: number, p: any) => sum + (p.income_per_tick || 0), 0);

  return (
    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-8">
      <div className="bg-slate-900 border-2 border-amber-900/50 shadow-2xl shadow-amber-900/20 max-w-4xl w-full max-h-full flex flex-col font-serif">
        <div className="p-4 border-b border-amber-900/30 bg-slate-800/50 flex justify-between items-center">
          <div>
            <h2 className="text-2xl text-amber-500 uppercase tracking-widest">Industrial Empire</h2>
            <div className="text-sm text-amber-600/70 font-mono mt-1">Manage Real Estate & Employees</div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-xs text-amber-600/70 font-mono uppercase">Vault Balance</div>
              <div className="text-xl text-amber-400 font-mono">{worldState.brass_coins || 0} <span className="text-amber-700 text-sm">COINS</span></div>
            </div>
            <div className="text-right">
              <div className="text-xs text-amber-600/70 font-mono uppercase">Passive Income</div>
              <div className="text-xl text-emerald-400 font-mono">+{totalIncome} <span className="text-emerald-700 text-sm">/TICK</span></div>
            </div>
            <button 
              onClick={onClose}
              className="text-amber-500 hover:text-amber-300 text-2xl px-2"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          <TutorialBox 
            title="Empire Management" 
            message="Purchase properties in the narrative by asking the Narrator. Owned properties generate passive Brass Coins over time. You can also ask the narrator to hire NPCs for your properties to gain additional benefits!" 
            isEnabled={character.show_tutorials} 
          />
          <div className="flex gap-6">
            <div className="flex-1">
              <h3 className="text-sm text-amber-600/70 font-mono uppercase tracking-widest mb-4 pb-2 border-b border-amber-900/30">Your Holdings</h3>
            {playerProperties.length === 0 ? (
              <div className="text-amber-100/40 text-center py-8 italic font-serif">
                You own no properties. Invest your brass to build an empire.
              </div>
            ) : (
              <div className="space-y-4">
                {playerProperties.map((p: any) => (
                  <div key={p.id} className="bg-slate-800 border border-emerald-900/30 p-4 rounded-sm relative overflow-hidden group">
                    <div className="absolute top-0 left-0 w-1 h-full bg-emerald-600/50"></div>
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-amber-300 font-serif text-lg">{p.name}</div>
                        <div className="text-xs text-amber-600/70 font-mono uppercase">{p.property_type}</div>
                      </div>
                      <div className="text-right text-sm font-mono">
                        <div className="text-emerald-400">+{p.income_per_tick} / tick</div>
                      </div>
                    </div>
                    <p className="text-xs text-amber-100/60 leading-relaxed mb-3">{p.description}</p>
                    <div className="text-xs text-amber-500/50 italic border-t border-slate-700 pt-2">
                      * Speak to the Narrator to manage employees for this property.
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex-1 border-l border-amber-900/30 pl-6">
            <h3 className="text-sm text-amber-600/70 font-mono uppercase tracking-widest mb-4 pb-2 border-b border-amber-900/30">Available Local Real Estate</h3>
            <div className="text-xs text-amber-500/70 mb-4 italic">
              These properties are available for purchase in {worldState.current_location?.name}. Ask the narrator to buy them!
            </div>
            
            <div className="space-y-4">
              {localProperties.filter((p: any) => p.owner_id !== worldState.player_stats?.id).map((p: any) => (
                <div key={p.id} className="bg-slate-800/50 border border-amber-900/20 p-4 rounded-sm relative">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="text-amber-200/80 font-serif text-lg">{p.name}</div>
                      <div className="text-xs text-amber-700 font-mono uppercase">{p.property_type}</div>
                    </div>
                    <div className="text-right text-sm font-mono">
                      <div className="text-rose-400">{p.price} Coins</div>
                      <div className="text-emerald-500/70 text-xs">+{p.income_per_tick} / tick</div>
                    </div>
                  </div>
                  <p className="text-xs text-amber-100/50 leading-relaxed">{p.description}</p>
                  {p.owner_id && <div className="text-xs text-rose-500/50 mt-2 font-mono">Owned by another</div>}
                </div>
              ))}
              {localProperties.filter((p: any) => p.owner_id !== worldState.player_stats?.id).length === 0 && (
                <div className="text-amber-100/40 text-center py-8 italic font-serif">
                  No properties available for purchase here.
                </div>
              )}
            </div>
          </div>
          </div>
        </div>
      </div>
    </div>
  );
}

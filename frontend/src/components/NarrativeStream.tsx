import { useEffect, useRef } from 'react';
import { Virtuoso } from 'react-virtuoso';
import type { GlossaryData } from '../api';
import { audioManager } from '../utils/AudioManager';

interface Message {
  id: string;
  sender: 'user' | 'narrator' | 'system';
  content: string;
  timestamp: string;
  mood?: string;
  isExploration?: boolean;
  stateUpdates?: any;
  events?: any[];
}

interface NarrativeStreamProps {
  messages: Message[];
  isLoading: boolean;
  glossary: GlossaryData | null;
  onOpenCombat?: () => void;
  onOpenMinigame?: () => void;
}

export default function NarrativeStream({
  messages,
  isLoading,
  glossary,
  onOpenCombat,
  onOpenMinigame
}: NarrativeStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      let extractedMood = lastMsg.mood;
      const moodMatch = lastMsg.content.match(/\[mood:(.*?)\]/i);
      if (moodMatch) {
        extractedMood = moodMatch[1].trim();
      }
      
      if (extractedMood) {
        audioManager.transitionScore(extractedMood);
      }
    }
  }, [messages]);

  const renderWithGlossary = (text: string, glossary: GlossaryData) => {
    if (!text) return text;
    
    const terms = [

      ...glossary.locations.map(l => ({ ...l, type: 'location' })),
      ...glossary.npcs.map(n => ({ ...n, type: 'npc' })),
      ...glossary.items.map(i => ({ ...i, type: 'item' }))
    ];
    
    if (!terms.length) return text;
    
    const sortedTerms = terms.sort((a, b) => b.name.length - a.name.length);
    const escapedTerms = sortedTerms.map(t => t.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const regex = new RegExp(`\\b(${escapedTerms.join('|')})\\b`, 'gi');
    
    const parts = text.split(regex);
    return parts.map((part, i) => {
      const termMatch = sortedTerms.find(t => t.name.toLowerCase() === part.toLowerCase());
      if (termMatch) {
         let colorClass = "text-amber-300";
         if (termMatch.type === "location") colorClass = "text-emerald-400";
         else if (termMatch.type === "npc") colorClass = "text-sky-400";
         
         return (
           <span 
             key={i} 
             className={`${colorClass} font-bold cursor-help underline decoration-dotted underline-offset-2 transition-colors hover:text-white`}
             title={`${termMatch.type.toUpperCase()}: ${termMatch.description || 'No description available'}`}
             onClick={() => {
               window.dispatchEvent(new CustomEvent('saos_ping_exploration'));
             }}
           >
             {part}
           </span>
         );
      }
      return part;
    });
  };

  return (
    <div className="flex-1 min-h-[300px] h-full flex flex-col relative w-full pr-2">
      <Virtuoso
        ref={scrollRef as any}
        data={messages}
        className="w-full h-full scrollbar-thin scrollbar-thumb-amber-700"
        initialTopMostItemIndex={messages.length - 1}
        followOutput="smooth"
        itemContent={(_index, msg) => (
          <div
            key={msg.id}
            className={`flex flex-col max-w-3xl mb-4 px-2 ${
              msg.sender === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'
            }`}
          >
            <div className="flex items-center gap-2 text-[10px] text-slate-400 mb-1 px-1">
              <span className="font-bold uppercase tracking-wider text-amber-500">
                {msg.sender === 'user' ? '👤 Player Action' : msg.sender === 'narrator' ? '📜 Narrator' : '⚠️ System'}
              </span>
              <span>•</span>
              <span>{msg.timestamp}</span>
              {msg.mood && (
                <span className="bg-amber-950 text-amber-300 border border-amber-700/50 px-1.5 py-0.5 rounded text-[9px]">
                  Mood: {msg.mood}
                </span>
              )}
              {msg.isExploration && (
                <span className="bg-sky-950 text-sky-300 border border-sky-700/50 px-1.5 py-0.5 rounded text-[9px]">
                  🔍 Exploration Mode
                </span>
              )}
            </div>

            <div
              className={`p-4 rounded-xl text-sm leading-relaxed whitespace-pre-wrap shadow-md border ${
                msg.sender === 'user'
                  ? 'bg-amber-950/40 border-amber-700/50 text-amber-100 rounded-tr-none'
                  : msg.sender === 'system'
                  ? 'bg-rose-950/30 border-rose-800/40 text-rose-200 rounded-tl-none'
                  : 'bg-slate-900/90 border-slate-700/60 text-slate-200 rounded-tl-none'
              } ${msg.mood ? `mood-${msg.mood}` : ''}`}
            >
              {glossary ? renderWithGlossary(msg.content, glossary) : msg.content}

              {msg.events && msg.events.length > 0 && msg.stateUpdates && (
                (msg.stateUpdates.empire_updates?.brass_coins_change !== 0 && msg.stateUpdates.empire_updates?.brass_coins_change !== undefined) ||
                (msg.stateUpdates.tool_durability_updates && msg.stateUpdates.tool_durability_updates.length > 0) ||
                (msg.stateUpdates.inventory_updates && Object.keys(msg.stateUpdates.inventory_updates).length > 0) ||
                (msg.stateUpdates.quest_updates && Object.keys(msg.stateUpdates.quest_updates).length > 0) ||
                msg.stateUpdates.combat_updates?.is_combat_active ||
                msg.stateUpdates.minigame_trigger
              ) && (
                <div className="mt-3 pt-2 border-t border-amber-900/40 flex flex-wrap gap-2 text-xs">
                  <span className="font-semibold text-amber-400">⚡ Dynamic Events:</span>
                  {msg.events.map((ev: any, idx: number) => (
                    <span key={idx} className="bg-amber-900/60 text-amber-200 px-2 py-0.5 rounded border border-amber-700/50">
                      {typeof ev === 'string' ? ev : JSON.stringify(ev)}
                    </span>
                  ))}
                </div>
              )}

              {msg.sender === 'narrator' && msg.stateUpdates && (
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  {msg.stateUpdates.empire_updates?.brass_coins_change !== undefined && msg.stateUpdates.empire_updates.brass_coins_change !== 0 && (
                    <span className={`px-2 py-0.5 rounded border ${msg.stateUpdates.empire_updates.brass_coins_change > 0 ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700/50' : 'bg-rose-900/60 text-rose-300 border-rose-700/50'}`}>
                      🪙 {msg.stateUpdates.empire_updates.brass_coins_change > 0 ? '+' : ''}{msg.stateUpdates.empire_updates.brass_coins_change} Coins
                    </span>
                  )}
                  {msg.stateUpdates.tool_durability_updates && msg.stateUpdates.tool_durability_updates.map((td: any, idx: number) => (
                    <span key={`td-${idx}`} className={`px-2 py-0.5 rounded border ${td.durability_change > 0 ? 'bg-emerald-900/60 text-emerald-300 border-emerald-700/50' : 'bg-rose-900/60 text-rose-300 border-rose-700/50'}`}>
                      🔧 {td.tool_name}: {td.durability_change > 0 ? '+' : ''}{td.durability_change} Durability
                    </span>
                  ))}
                </div>
              )}

              {msg.sender === 'narrator' && msg.stateUpdates?.combat_updates?.is_combat_active && onOpenCombat && (
                <div className="mt-3 pt-2 border-t border-amber-900/40 flex justify-end">
                  <button 
                    onClick={onOpenCombat}
                    className="px-3 py-1.5 bg-red-900/50 hover:bg-red-800 text-red-200 text-xs font-mono uppercase tracking-widest border border-red-700/50 rounded flex items-center gap-2 transition-colors"
                  >
                    ⚔️ Enter Combat
                  </button>
                </div>
              )}

              {msg.sender === 'narrator' && msg.stateUpdates?.minigame_trigger && onOpenMinigame && (
                <div className="mt-3 pt-2 border-t border-amber-900/40 flex justify-end">
                  <button 
                    onClick={onOpenMinigame}
                    className="px-3 py-1.5 bg-cyan-900/50 hover:bg-cyan-800 text-cyan-200 text-xs font-mono uppercase tracking-widest border border-cyan-700/50 rounded flex items-center gap-2 transition-colors"
                  >
                    ⚙️ Start Minigame
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      />

      {isLoading && (
        <div className="flex items-center gap-3 text-amber-400/80 p-3 bg-slate-900/60 rounded-lg border border-amber-800/30 w-fit">
          <div className="w-4 h-4 rounded-full border-2 border-amber-500 border-t-transparent animate-spin"></div>
          <span className="text-xs animate-pulse">Consulting the Steam Engine & vLLM...</span>
        </div>
      )}
    </div>
  );
}

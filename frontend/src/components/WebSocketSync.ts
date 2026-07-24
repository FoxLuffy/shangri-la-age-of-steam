import { useEffect } from 'react';
import { WS_URL } from '../api';
import { useGameStore } from '../stores/gameStore';

interface WebSocketSyncProps {
  clientId: string;
  characterId?: number;
  onOpenMinigame?: () => void;
  loadState: () => void;
}

export function WebSocketSync({ clientId, characterId, onOpenMinigame, loadState }: WebSocketSyncProps) {
  const setActiveNpcs = useGameStore(state => state.setActiveNpcs);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'market_sync') {
          window.dispatchEvent(new CustomEvent('saos_market_sync', { detail: msg }));
        } else if (msg.type === 'global_event') {
          const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          window.dispatchEvent(new CustomEvent('saos_global_event', { detail: { event: msg.event, timestamp: now } }));
        } else if (msg.type === 'trigger_minigame') {
          if (msg.character_id === characterId && onOpenMinigame) {
            onOpenMinigame();
          }
        } else if (msg.type === 'narrative_event' && msg.action && msg.action.client_id !== clientId) {
          window.dispatchEvent(new CustomEvent('saos_peer_event', { detail: msg }));
          loadState();
        } else if (msg.type === 'npc_state_change') {
          setActiveNpcs((prev) => {
            const isDead = msg.npc.hp <= 0 || (msg.npc.traits && msg.npc.traits.some((t: string) => t.toLowerCase() === 'dead'));
            if (isDead) {
              return prev.filter((n) => n.id !== msg.npc.id);
            }
            const exists = prev.find((n) => n.id === msg.npc.id);
            if (exists) {
              return prev.map((n) => n.id === msg.npc.id ? msg.npc : n);
            }
            return [...prev, msg.npc];
          });
        }
      } catch (err) {
        console.error('WS parse error', err);
      }
    };
    return () => {
      ws.close();
    };
  }, [clientId, characterId, onOpenMinigame, loadState, setActiveNpcs]);

  return null;
}

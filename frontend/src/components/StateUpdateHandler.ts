import { useEffect } from 'react';
import { useGameStore } from '../stores/gameStore';

export function StateUpdateHandler() {
  const updateState = useGameStore((state) => state.updateState);

  useEffect(() => {
    const handleStateUpdate = (e: CustomEvent) => {
      const { detail } = e;
      if (detail && detail.state) {
        updateState({
          currentLocationId: detail.state.current_location_id,
          currentLocation: detail.state.current_location,
          activeNpcs: detail.state.active_npcs || [],
          globalEvent: detail.state.global_event || '',
          combatState: detail.state.combat_state || null,
          isMinigameActive: !!detail.state.active_minigame,
        });
      }
    };
    
    window.addEventListener('saos_state_update' as any, handleStateUpdate);
    return () => window.removeEventListener('saos_state_update' as any, handleStateUpdate);
  }, [updateState]);

  return null;
}

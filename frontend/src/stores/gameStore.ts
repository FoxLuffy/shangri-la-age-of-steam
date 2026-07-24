import { create } from 'zustand';
import { type Location, type NPC } from '../api';

interface GameState {
  characterId: number | null;
  currentLocationId: string;
  currentLocation: Location | null;
  allLocations: Location[];
  activeNpcs: NPC[];
  activePlayers: any[];
  globalEvent: string;
  combatState: any;
  inventory: any[];
  quests: any[];
  isMinigameActive: boolean;
  marketPrices: Record<string, number>;
  
  setCharacterId: (id: number | null) => void;
  setCurrentLocationId: (id: string) => void;
  setCurrentLocation: (loc: Location | null) => void;
  setAllLocations: (locs: Location[]) => void;
  setActiveNpcs: (npcs: NPC[] | ((prev: NPC[]) => NPC[])) => void;
  setActivePlayers: (players: any[]) => void;
  setGlobalEvent: (event: string) => void;
  setCombatState: (state: any) => void;
  setInventory: (inv: any[]) => void;
  setQuests: (quests: any[]) => void;
  setIsMinigameActive: (active: boolean) => void;
  setMarketPrices: (prices: Record<string, number>) => void;
  updateState: (partialState: Partial<GameState>) => void;
}

export const useGameStore = create<GameState>((set) => ({
  characterId: null,
  currentLocationId: '1',
  currentLocation: null,
  allLocations: [],
  activeNpcs: [],
  activePlayers: [],
  globalEvent: '',
  combatState: null,
  inventory: [],
  quests: [],
  isMinigameActive: false,
  marketPrices: {},

  setCharacterId: (id) => set({ characterId: id }),
  setCurrentLocationId: (id) => set({ currentLocationId: id }),
  setCurrentLocation: (loc) => set({ currentLocation: loc }),
  setAllLocations: (locs) => set({ allLocations: locs }),
  setActiveNpcs: (updater) => set((state) => ({ 
    activeNpcs: typeof updater === 'function' ? updater(state.activeNpcs) : updater 
  })),
  setActivePlayers: (players) => set({ activePlayers: players }),
  setGlobalEvent: (event) => set({ globalEvent: event }),
  setCombatState: (combatState) => set({ combatState }),
  setInventory: (inventory) => set({ inventory }),
  setQuests: (quests) => set({ quests }),
  setIsMinigameActive: (isMinigameActive) => set({ isMinigameActive }),
  setMarketPrices: (marketPrices) => set({ marketPrices }),
  updateState: (partialState) => set((state) => ({ ...state, ...partialState })),
}));

import axios from 'axios';
import { useQuery } from '@tanstack/react-query';
console.log("Cache buster: v3");
export let BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '__VITE_BACKEND_URL__';

// If the environment variable wasn't replaced by Docker at runtime, or is empty, use the smart router
if (!BACKEND_URL || BACKEND_URL.startsWith('__VITE_')) {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Local development (localhost, IPs, or Codespaces)
    if (hostname === 'localhost' || hostname.match(/^\d+\.\d+\.\d+\.\d+$/) || hostname.match(/^\d+-/)) {
      BACKEND_URL = `${window.location.protocol}//${hostname.replace(/^\d+-/, '8003-')}:8003`;
    } else {
      // Generic production domain fallback
      BACKEND_URL = `https://api.${hostname}`;
    }
  } else {
    BACKEND_URL = 'http://localhost:8003';
  }
}

export const WS_URL = BACKEND_URL.replace(/^http/, 'ws') + '/ws';

const api = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PlayerActionPayload {
  action_text: string;
  current_location_id: string;
  mood?: string;
  is_exploration?: boolean;
  context_type?: string;
  client_id?: string;
  character_id?: number;
}

export interface NPC {
  id: string;
  name: string;
  traits: string[];
  current_dialogue?: string;
  disposition: number;
  memories: { key: string; value: string }[];
  location_id?: string;
}

export interface Location {
  id: string;
  name: string;
  description: string;
  lore_text?: string;
  npcs: string[];
  faction_id?: string | null;
}

export interface WorldStateData {
  current_location_id: string;
  active_npcs_ids: string[];
  global_event?: string;
  time_period?: string;
  weather?: string;
  world_memories?: { key: string; value: string }[];
  current_location: Location;
  active_npcs: NPC[];
  inventory?: any[];
  quests?: any[];
  active_minigame?: any;
  is_combat_active?: boolean;
  combat_state?: any;
}

export interface GetStateResponse {
  state: WorldStateData;
  all_locations: Location[];
  all_npcs: NPC[];
  active_players?: any[];
}

export interface GlossaryItem {
  id: string | number;
  name: string;
  description?: string;
}

export interface GlossaryData {
  locations: GlossaryItem[];
  npcs: GlossaryItem[];
  items: GlossaryItem[];
}

export interface Character {
  id: number;
  name: string;
  character_class: string;
  background: string;
  stats: {
    strength: number;
    intellect: number;
    charm: number;
  };
  show_tutorials: boolean;
  active_bounties?: number[];
  completed_bounties?: number[];
  // Save metadata (populated by GET /sessions/{user_id}).
  has_save?: boolean;
  last_saved?: string | null;
  location_name?: string | null;
}

export const fetchCharacter = async (characterId: number): Promise<Character> => {
  const { data } = await api.get(`/characters/${characterId}`);
  return data;
};

export const fetchSessions = async (userId: number): Promise<Character[]> => {
  const { data } = await api.get(`/sessions/${userId}`);
  return data;
};

export const createCharacter = async (
  name: string,
  preset: string,
  origin: string = "",
  backstory: string = "",
  gearPrompt: string = "",
  showTutorials: boolean = true,
  gear: any[] = [],
  userId?: number | null
): Promise<Character> => {
  const { data } = await api.post('/characters', { 
    name, 
    preset, 
    origin,
    backstory, 
    gear_prompt: gearPrompt, 
    show_tutorials: showTutorials, 
    gear,
    user_id: userId
  });
  return data;
};

export const generateGear = async (preset: string, gearPrompt: string): Promise<any[]> => {
  const { data } = await api.post('/characters/generate-gear', { preset, gear_prompt: gearPrompt });
  return data.items || [];
};

export const getMarket = async () => {
  const { data } = await api.get('/market');
  return data;
};

export const tradeMarket = async (characterId: number, resourceName: string, quantity: number, action: string) => {
  const { data } = await api.post(`/market/trade?character_id=${characterId}`, {
    resource_name: resourceName,
    quantity,
    action
  });
  return data;
};

export const toggleTutorials = async (characterId: number, showTutorials: boolean): Promise<{status: string, show_tutorials: boolean}> => {
  const { data } = await api.post(`/characters/${characterId}/settings/tutorials`, { show_tutorials: showTutorials });
  return data;
};

export const fetchHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const fetchGlossary = async (): Promise<GlossaryData> => {
  const { data } = await api.get('/glossary');
  return data;
};

export const fetchWorldState = async (characterId?: number): Promise<GetStateResponse> => {
  const { data } = await api.get('/state' + (characterId ? `?character_id=${characterId}` : ''));
  return data;
};

export const sendAction = async (
  payload: PlayerActionPayload,
  onChunk?: (chunk: string) => void
) => {
  const response = await fetch(`${BACKEND_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('ReadableStream not supported.');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let finalResult = null;

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim();
          if (dataStr) {
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.chunk && onChunk) {
                const speedSetting = localStorage.getItem('saos_narrator_speed') || 'Fast';
                let delay = 0;
                if (speedSetting === 'Normal') delay = 50;
                if (speedSetting === 'Slow') delay = 120;
                
                if (delay > 0) {
                  await new Promise(r => setTimeout(r, delay));
                }
                onChunk(parsed.chunk);
              } else if (parsed.result) {
                finalResult = parsed.result;
              }
            } catch (e) {
              console.error('Error parsing chunk:', e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return finalResult;
};

export interface LedgerEntry {
  id: number;
  timestamp: string;
  action: string;
  narration: string;
  state_updates?: any;
  events?: any[];
  location_id?: string;
}

export async function fetchHistory(limit: number = 50): Promise<LedgerEntry[]> {
  const response = await fetch(`${BACKEND_URL}/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }
  return response.json();
}

export const resetWorldState = async () => {
  const { data } = await api.post('/reset');
  return data;
};

export const importWorldState = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

export const uploadModData = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/modding/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return data;
};

export interface WorkshopMod {
  id: string;
  name: string;
  description: string;
  author: string;
  downloads: number;
  avg_rating: number;
  rating_count: number;
  featured: boolean;
  dependencies?: string[];
}

export interface ModReview {
  user_id: number;
  stars: number;
  review: string | null;
  created_at: string;
}

export const fetchWorkshopMods = async (): Promise<WorkshopMod[]> => {
  const { data } = await api.get('/workshop/mods');
  return data;
};

export const installWorkshopMod = async (modId: string) => {
  const { data } = await api.post(`/workshop/mods/${modId}/install`);
  return data;
};

export const rateMod = async (modId: string, userId: number, stars: number, review?: string) => {
  const { data } = await api.post(`/workshop/mods/${modId}/rate`, { user_id: userId, stars, review });
  return data;
};

export const fetchModRatings = async (modId: string): Promise<ModReview[]> => {
  const { data } = await api.get(`/workshop/mods/${modId}/ratings`);
  return data;
};
export const useWorldStateQuery = (characterId?: number) => {
  return useQuery({
    queryKey: ['worldState', characterId],
    queryFn: () => fetchWorldState(characterId),
    staleTime: 5000,
  });
};

export const useGlossaryQuery = () => {
  return useQuery({
    queryKey: ['glossary'],
    queryFn: fetchGlossary,
    staleTime: Infinity,
  });
};

export const useMarketQuery = () => {
  return useQuery({
    queryKey: ['market'],
    queryFn: getMarket,
    staleTime: 30000,
  });
};

export const fetchCodex = async () => {
  const { data } = await api.get('/codex');
  return data;
};

export const useCodexQuery = () => {
  return useQuery({
    queryKey: ['codex'],
    queryFn: fetchCodex,
    staleTime: Infinity,
  });
};

export const fetchAirship = async (characterId: number) => {
  try {
    const { data } = await api.get(`/gameplay/airships?character_id=${characterId}`);
    return data;
  } catch (e) {
    return null;
  }
};

export const navigateAirship = async (characterId: number, locationId: string) => {
  const { data } = await api.post(`/gameplay/airships/navigate`, {
    character_id: characterId,
    location_id: locationId
  });
  return data;
};

export const fetchGuildTreasury = async (guildId: number) => {
  const { data } = await api.get(`/gameplay/guilds/treasury?guild_id=${guildId}`);
  return data;
};

export const createGuild = async (characterId: number, name: string, description: string) => {
  const { data } = await api.post(`/gameplay/guilds/create?character_id=${characterId}`, { name, description });
  return data;
};

export const inviteGuild = async (leaderId: number, guildId: number, characterId: number) => {
  const { data } = await api.post(`/gameplay/guilds/invite?leader_id=${leaderId}`, { guild_id: guildId, character_id: characterId });
  return data;
};

export const fetchMessages = async (locationId: string) => {
  const { data } = await api.get(`/gameplay/messages/board?location_id=${locationId}`);
  return data;
};

export const sendMessage = async (characterId: number, locationId: string, content: string) => {
  const { data } = await api.post(`/gameplay/messages/send?character_id=${characterId}`, { location_id: locationId, content });
  return data;
};

// --- Save State Management (single slot per character) ---

export interface SaveMeta {
  id: number;
  character_id: number;
  name: string;
  created_at: string;
}

export const createSave = async (characterId: number, name?: string): Promise<SaveMeta> => {
  const { data } = await api.post('/saves', { character_id: characterId, name });
  return data;
};

export const getSave = async (characterId: number): Promise<SaveMeta> => {
  const { data } = await api.get(`/saves/${characterId}`);
  return data;
};

export const loadSave = async (characterId: number) => {
  const { data } = await api.get(`/saves/${characterId}/load`);
  return data;
};

export const deleteSave = async (characterId: number) => {
  const { data } = await api.delete(`/saves/${characterId}`);
  return data;
};

export interface SaveExport {
  schema_version: number;
  name: string;
  created_at: string;
  snapshot: {
    character: Record<string, unknown>;
    world: Record<string, unknown> | null;
    inventory: { item_id: number; quantity: number; durability?: number | null }[];
    quests: { quest_id: number; state: string }[];
  };
}

export const exportSave = async (characterId: number): Promise<SaveExport> => {
  const { data } = await api.get(`/saves/${characterId}/export`);
  return data;
};

export const importSave = async (characterId: number, payload: SaveExport): Promise<SaveMeta> => {
  const { data } = await api.post(`/saves/${characterId}/import`, payload);
  return data;
};

// --- Crafting (C3.1–C3.3) ---

export interface RecipeRequirement {
  item_id: number;
  name: string | null;
  quantity: number;
}

export interface KnownRecipeInfo {
  recipe_id: number;
  name: string;
  method: string;
  branch: string | null;
  tier: number;
  result_item_id: number;
  result_name: string | null;
  requirements: RecipeRequirement[];
}

export interface CraftingMaterial {
  item_id: number;
  name: string | null;
  quantity: number;
}

export interface CraftingProficiency {
  branch: string;
  level: number;
  xp: number;
}

export const getKnownRecipes = async (characterId: number): Promise<KnownRecipeInfo[]> => {
  const { data } = await api.get(`/crafting/known?character_id=${characterId}`);
  return data;
};

export const getCraftingMaterials = async (characterId: number): Promise<CraftingMaterial[]> => {
  const { data } = await api.get(`/crafting/materials?character_id=${characterId}`);
  return data;
};

export const getProficiency = async (characterId: number): Promise<CraftingProficiency[]> => {
  const { data } = await api.get(`/crafting/proficiency?character_id=${characterId}`);
  return data;
};

export const craftItem = async (characterId: number, recipeId: number) => {
  const { data } = await api.post(`/craft?character_id=${characterId}&recipe_id=${recipeId}`);
  return data;
};

export const experimentCraft = async (characterId: number, itemIds: number[]) => {
  const { data } = await api.post('/crafting/experiment', { character_id: characterId, item_ids: itemIds });
  return data;
};

export function craftSuccessPct(level: number, tier: number, branch: string | null): number {
  if (!branch) return 100;
  const c = Math.max(0.05, Math.min(0.98, 0.5 + 0.1 * (level - tier)));
  return Math.round(c * 100);
}

// --- Bounties (CR2) ---

export interface Bounty {
  id: number;
  title: string;
  description: string;
  target_npc_type: string;
  reward_coins: number;
  status: string;
}

export interface BountyBoardData {
  available: Bounty[];
  active_ids: number[];
  completed_ids: number[];
}

export const fetchBounties = async (characterId: number): Promise<BountyBoardData> => {
  const { data } = await api.get(`/gameplay/bounties?character_id=${characterId}`);
  return data;
};

export const acceptBounty = async (characterId: number, bountyId: number) => {
  const { data } = await api.post(`/gameplay/bounties/accept?character_id=${characterId}`, { bounty_id: bountyId });
  return data;
};

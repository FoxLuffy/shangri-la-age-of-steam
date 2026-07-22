import axios from 'axios';
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
  npcs: string[];
}

export interface WorldStateData {
  current_location_id: string;
  active_npcs_ids: string[];
  global_event?: string;
  world_memories?: { key: string; value: string }[];
  current_location: Location;
  active_npcs: NPC[];
  inventory?: any[];
  quests?: any[];
  active_minigame?: any;
  is_combat_active?: boolean;
}

export interface GetStateResponse {
  state: WorldStateData;
  all_locations: Location[];
  all_npcs: NPC[];
  active_players?: any[];
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
}

export const fetchCharacter = async (characterId: number): Promise<Character> => {
  const { data } = await api.get(`/characters/${characterId}`);
  return data;
};

export const createCharacter = async (
  name: string,
  preset: string,
  backstory: string = "",
  gearPrompt: string = "",
  showTutorials: boolean = true,
  gear: any[] = [],
  userId?: number | null
): Promise<Character> => {
  const { data } = await api.post('/characters', { 
    name, 
    preset, 
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


import axios from 'axios';
export let BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8003';

if (typeof window !== 'undefined' && !import.meta.env.VITE_BACKEND_URL) {
  if (window.location.hostname.match(/^\d+-/)) {
    BACKEND_URL = `${window.location.protocol}//${window.location.hostname.replace(/^\d+-/, '8003-')}`;
  } else {
    BACKEND_URL = `${window.location.protocol}//${window.location.hostname}:8003`;
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
}

export interface GetStateResponse {
  state: WorldStateData;
  all_locations: Location[];
  all_npcs: NPC[];
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

export const createCharacter = async (name: string, preset: string, gearPrompt: string = "", showTutorials: boolean = true, gear: any[] = []): Promise<Character> => {
  const { data } = await api.post('/characters', { name, preset, gear_prompt: gearPrompt, show_tutorials: showTutorials, gear });
  return data;
};

export const generateGear = async (preset: string, gearPrompt: string): Promise<any[]> => {
  const { data } = await api.post('/characters/generate-gear', { preset, gear_prompt: gearPrompt });
  return data.items || [];
};

export const toggleTutorials = async (characterId: number, showTutorials: boolean): Promise<{status: string, show_tutorials: boolean}> => {
  const { data } = await api.post(`/characters/${characterId}/settings/tutorials`, { show_tutorials: showTutorials });
  return data;
};

export const fetchHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const fetchWorldState = async (): Promise<GetStateResponse> => {
  const { data } = await api.get('/state');
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


import axios from 'axios';
let BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8003';

if (typeof window !== 'undefined' && !import.meta.env.VITE_BACKEND_URL) {
  if (window.location.hostname.match(/^\d+-/)) {
    BACKEND_URL = `${window.location.protocol}//${window.location.hostname.replace(/^\d+-/, '8003-')}`;
  } else {
    BACKEND_URL = `${window.location.protocol}//${window.location.hostname}:8003`;
  }
}

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
  current_location?: Location;
  active_npcs?: NPC[];
}

export interface GetStateResponse {
  state: WorldStateData;
  all_locations: Location[];
  all_npcs: NPC[];
}

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

export const resetWorldState = async () => {
  const { data } = await api.post('/reset');
  return data;
};

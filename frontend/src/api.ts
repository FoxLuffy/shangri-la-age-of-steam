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

export const sendAction = async (payload: PlayerActionPayload) => {
  const { data } = await api.post('/chat', payload);
  return data;
};

export const resetWorldState = async () => {
  const { data } = await api.post('/reset');
  return data;
};

import axios from 'axios';

const getBaseURL = () => {
  if (import.meta.env.VITE_BACKEND_URL) {
    return import.meta.env.VITE_BACKEND_URL;
  }
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:8000`;
  }
  return 'http://localhost:8000';
};

const api = axios.create({
  baseURL: getBaseURL(),
});

export const fetchHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const fetchState = async () => {
  const { data } = await api.get('/state');
  return data;
};

export const sendAction = async (actionText: string, mood?: string, isExploration?: boolean) => {
  const { data } = await api.post('/chat', {
    action_text: actionText,
    mood: mood || null,
    is_exploration: isExploration || false
  });
  return data;
};

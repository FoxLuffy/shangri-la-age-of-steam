import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const fetchHealth = async () => {
  const { data } = await api.get('/health');
  return data;
};

export const sendAction = async (action: string) => {
  const { data } = await api.post('/chat', { action });
  return data;
};

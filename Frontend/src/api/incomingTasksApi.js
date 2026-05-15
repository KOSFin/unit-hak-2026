import { apiClient } from './client';

export async function getIncomingTasks() {
  const { data } = await apiClient.get('/api/incoming-tasks');
  return data;
}

export async function createIncomingTask(payload) {
  const { data } = await apiClient.post('/api/incoming-tasks', payload);
  return data;
}

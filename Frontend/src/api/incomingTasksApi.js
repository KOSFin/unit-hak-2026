import { apiClient, boardParams } from './client';

export async function getIncomingTasks(boardId = null) {
  const { data } = await apiClient.get('/api/incoming-tasks', {
    params: boardParams(boardId),
  });
  return data;
}

export async function createIncomingTask(payload) {
  const { data } = await apiClient.post('/api/incoming-tasks', payload);
  return data;
}

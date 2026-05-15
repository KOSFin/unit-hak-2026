import { apiClient } from './client';

export async function getTasks(boardId) {
  const { data } = await apiClient.get('/api/tasks', {
    params: boardId ? { board_id: boardId } : undefined,
  });
  return data;
}

export async function getTask(taskId) {
  const { data } = await apiClient.get(`/api/tasks/${taskId}`);
  return data;
}

export async function createTask(payload) {
  const { data } = await apiClient.post('/api/tasks', payload);
  return data;
}

export async function updateTask(taskId, payload) {
  const { data } = await apiClient.patch(`/api/tasks/${taskId}`, payload);
  return data;
}

export async function deleteTask(taskId) {
  const { data } = await apiClient.delete(`/api/tasks/${taskId}`);
  return data;
}

export async function moveTask(taskId, payload) {
  const { data } = await apiClient.patch(`/api/tasks/${taskId}/move`, payload);
  return data;
}

import { apiClient } from './client';

export async function createColumn(payload) {
  const { data } = await apiClient.post('/api/columns', payload);
  return data;
}

export async function updateColumn(columnId, payload) {
  const { data } = await apiClient.patch(`/api/columns/${columnId}`, payload);
  return data;
}

export async function deleteColumn(columnId) {
  const { data } = await apiClient.delete(`/api/columns/${columnId}`);
  return data;
}

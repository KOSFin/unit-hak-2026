import { apiClient, boardParams } from './client';

export async function getColumns(boardId) {
  const { data } = await apiClient.get('/api/columns', { params: boardParams(boardId) });
  return data;
}

export async function createColumn(payload) {
  const { data } = await apiClient.post('/api/columns', payload);
  return data;
}

export async function updateColumn(columnId, payload) {
  const { data } = await apiClient.patch(`/api/columns/${columnId}`, payload);
  return data;
}

export async function deleteColumn(columnId, boardId) {
  const { data } = await apiClient.delete(`/api/columns/${columnId}`, { params: boardParams(boardId) });
  return data;
}

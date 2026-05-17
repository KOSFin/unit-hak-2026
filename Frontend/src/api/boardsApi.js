import { apiClient } from './client';

export async function createBoard(payload) {
  const { data } = await apiClient.post('/api/boards', payload);
  return data;
}

export async function getBoard(publicBoardId) {
  const { data } = await apiClient.get(`/api/boards/${publicBoardId}`);
  return data;
}

export async function updateBoard(publicBoardId, payload) {
  const { data } = await apiClient.patch(`/api/boards/${publicBoardId}`, payload);
  return data;
}

export async function deleteBoard(publicBoardId) {
  await apiClient.delete(`/api/boards/${publicBoardId}`);
}

export async function getBoardEvents(publicBoardId, limit = 50) {
  const { data } = await apiClient.get(`/api/boards/${publicBoardId}/events`, {
    params: { limit },
  });
  return data;
}

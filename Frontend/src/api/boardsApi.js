import { apiClient } from './client';

export async function getDefaultBoard() {
  const { data } = await apiClient.get('/api/boards/default');
  return data;
}

export async function getBoard(boardId) {
  const { data } = await apiClient.get(`/api/boards/${boardId}`);
  return data;
}

import { apiClient, boardParams } from './client';

export async function getRules(boardId) {
  const { data } = await apiClient.get('/api/rules', { params: boardParams(boardId) });
  return data;
}

export async function createRule(payload) {
  const { data } = await apiClient.post('/api/rules', payload);
  return data;
}

export async function updateRule(ruleId, payload) {
  const { data } = await apiClient.patch(`/api/rules/${ruleId}`, payload);
  return data;
}

export async function deleteRule(ruleId, boardId) {
  const { data } = await apiClient.delete(`/api/rules/${ruleId}`, { params: boardParams(boardId) });
  return data;
}

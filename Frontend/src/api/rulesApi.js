import { apiClient } from './client';

export async function getRules() {
  const { data } = await apiClient.get('/api/automation-rules');
  return data;
}

export async function createRule(payload) {
  const { data } = await apiClient.post('/api/automation-rules', payload);
  return data;
}

export async function updateRule(ruleId, payload) {
  const { data } = await apiClient.patch(`/api/automation-rules/${ruleId}`, payload);
  return data;
}

export async function deleteRule(ruleId) {
  const { data } = await apiClient.delete(`/api/automation-rules/${ruleId}`);
  return data;
}

import { apiClient } from './client';

export async function createGuestProfile(payload) {
  const { data } = await apiClient.post('/api/guests/profile', payload);
  return data;
}

export async function updateGuestProfile(guestId, payload) {
  const { data } = await apiClient.put(`/api/guests/${guestId}/profile`, payload);
  return data;
}

import { apiClient, boardParams } from './client';

export async function getNotifications(boardId) {
  const { data } = await apiClient.get('/api/notifications', { params: boardParams(boardId) });
  return data;
}

export async function markNotificationRead(notificationId, boardId) {
  const { data } = await apiClient.post(`/api/notifications/${notificationId}/read`, null, { params: boardParams(boardId) });
  return data;
}

export async function markAllNotificationsRead(boardId) {
  const { data } = await apiClient.post('/api/notifications/read-all', null, { params: boardParams(boardId) });
  return data;
}

export async function testNotification(payload) {
  const { data } = await apiClient.post('/api/notifications/test', payload);
  return data;
}

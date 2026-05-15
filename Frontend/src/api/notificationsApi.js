import { apiClient } from './client';

export async function getNotifications(unreadOnly = false) {
  const { data } = await apiClient.get('/api/notifications', {
    params: unreadOnly ? { unread_only: true } : undefined,
  });
  return data;
}

export async function markNotificationRead(notificationId) {
  const { data } = await apiClient.patch(`/api/notifications/${notificationId}/read`);
  return data;
}

export async function markAllNotificationsRead() {
  const { data } = await apiClient.post('/api/notifications/mark-all-read');
  return data;
}

import { apiClient, boardParams } from './client';

export async function getNotifications(unreadOnly = false, boardId = null) {
  const { data } = await apiClient.get('/api/notifications', {
    params: {
      ...(unreadOnly ? { unread_only: true } : {}),
      ...(boardParams(boardId) ?? {}),
    },
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

import { apiClient, resolveAppUrl } from './client';

export async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await apiClient.post('/api/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return {
    ...data,
    url: resolveAppUrl(data.url),
    path: data.path ?? data.url,
  };
}

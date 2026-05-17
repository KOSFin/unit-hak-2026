import { apiClient, resolveAppUrl } from './client';
import { compressImageBeforeUpload } from '../utils/imageUpload';

export async function uploadImage(file) {
  const preparedFile = await compressImageBeforeUpload(file);
  const formData = new FormData();
  formData.append('file', preparedFile);

  const { data } = await apiClient.post('/api/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return {
    ...data,
    url: resolveAppUrl(data.url),
    path: data.path ?? data.url,
  };
}

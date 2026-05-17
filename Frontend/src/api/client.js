import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
const APP_BASE_PATH = (import.meta.env.BASE_URL ?? '/').replace(/\/$/, '');

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function boardParams(boardId) {
  return boardId ? { board_id: boardId } : undefined;
}

export function getBoardPublicUrl(publicBoardId) {
  const base = import.meta.env.VITE_PUBLIC_BOARD_URL_BASE;
  if (base) {
    return `${base.replace(/\/$/, '')}/board/${publicBoardId}`;
  }
  return `/board/${publicBoardId}`;
}

export function resolveAppUrl(url) {
  if (!url) {
    return window.location.origin;
  }
  if (/^https?:\/\//i.test(url)) {
    return url;
  }

  const normalized = url.startsWith('/') ? url : `/${url}`;
  if (APP_BASE_PATH && APP_BASE_PATH !== '/' && normalized.startsWith(`${APP_BASE_PATH}/`)) {
    return `${window.location.origin}${normalized}`;
  }
  return `${window.location.origin}${APP_BASE_PATH}${normalized}`.replace(/(?<!:)\/{2,}/g, '/');
}

export function getErrorMessage(error, fallback = 'Unexpected error') {
  if (error?.response?.data?.detail) {
    const detail = error.response.data.detail;
    return typeof detail === 'string' ? detail : fallback;
  }

  if (error?.message) {
    return error.message;
  }

  return fallback;
}

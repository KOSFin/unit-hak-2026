import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

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
  return base ? `${base.replace(/\/$/, '')}/board/${publicBoardId}` : `/board/${publicBoardId}`;
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

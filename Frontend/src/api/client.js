// Central API client – reads VITE_API_URL from env (defaults to empty = same origin)
const BASE = import.meta.env.VITE_API_URL ?? '';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const err = new Error(detail.detail ?? `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

// Boards
export const api = {
  // Boards
  getBoards: () => request('/api/boards'),
  createBoard: (name) => request('/api/boards', { method: 'POST', body: JSON.stringify({ name }) }),
  getBoard: (id) => request(`/api/boards/${id}`),
  updateBoard: (id, name) => request(`/api/boards/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  deleteBoard: (id) => request(`/api/boards/${id}`, { method: 'DELETE' }),

  // Columns
  getColumns: (boardId) => request(`/api/boards/${boardId}/columns`),
  createColumn: (boardId, data) => request(`/api/boards/${boardId}/columns`, { method: 'POST', body: JSON.stringify(data) }),
  updateColumn: (boardId, colId, data) => request(`/api/boards/${boardId}/columns/${colId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteColumn: (boardId, colId) => request(`/api/boards/${boardId}/columns/${colId}`, { method: 'DELETE' }),

  // Tasks
  getTasks: (boardId) => request(`/api/boards/${boardId}/tasks`),
  createTask: (boardId, data) => request(`/api/boards/${boardId}/tasks`, { method: 'POST', body: JSON.stringify(data) }),
  getTask: (boardId, taskId) => request(`/api/boards/${boardId}/tasks/${taskId}`),
  updateTask: (boardId, taskId, data) => request(`/api/boards/${boardId}/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTask: (boardId, taskId) => request(`/api/boards/${boardId}/tasks/${taskId}`, { method: 'DELETE' }),
  moveTask: (boardId, taskId, data) => request(`/api/boards/${boardId}/tasks/${taskId}/move`, { method: 'POST', body: JSON.stringify(data) }),

  // Notifications
  getNotifications: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request(`/api/notifications${q ? '?' + q : ''}`);
  },
  markNotificationRead: (id) => request(`/api/notifications/${id}/read`, { method: 'PATCH' }),

  // Incoming Tasks
  getIncomingTasks: () => request('/api/incoming-tasks'),
  acceptIncomingTask: (id) => request(`/api/incoming-tasks/${id}/accept`, { method: 'PATCH' }),
  rejectIncomingTask: (id) => request(`/api/incoming-tasks/${id}/reject`, { method: 'PATCH' }),

  // Health
  health: () => request('/health'),
};

const FALLBACK_WS_URL = 'ws://localhost:8000/ws';

export function createRealtimeSocket(handlers) {
  const target = import.meta.env.VITE_WS_URL ?? FALLBACK_WS_URL;
  const socket = new WebSocket(target);

  socket.addEventListener('open', () => {
    handlers.onOpen?.();
  });

  socket.addEventListener('close', () => {
    handlers.onClose?.();
  });

  socket.addEventListener('error', () => {
    handlers.onError?.();
  });

  socket.addEventListener('message', (event) => {
    try {
      handlers.onMessage?.(JSON.parse(event.data));
    } catch {
      handlers.onInvalidMessage?.(event.data);
    }
  });

  return socket;
}

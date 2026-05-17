export function createRealtimeSocket(handlers) {
  const fallbackProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const fallbackTarget = `${fallbackProtocol}//${window.location.host}/ws`;
  const target = import.meta.env.VITE_WS_URL ?? fallbackTarget;
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

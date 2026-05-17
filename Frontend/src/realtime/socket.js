function normalizeSocketUrl(rawUrl, fallbackPath = '/ws') {
  if (rawUrl) {
    return rawUrl;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${fallbackPath}`;
}

function buildCandidateUrls() {
  const explicitUrl = import.meta.env.VITE_WS_URL;
  const explicitCandidates = explicitUrl ? [explicitUrl] : [];
  const fallbackCandidates = [normalizeSocketUrl('', '/ws'), normalizeSocketUrl('', '/api/ws')];
  return [...new Set([...explicitCandidates, ...fallbackCandidates])];
}

export function createRealtimeSocket(handlers = {}) {
  const candidates = buildCandidateUrls();
  let socket = null;
  let candidateIndex = 0;
  let reconnectTimer = null;
  let manuallyClosed = false;

  const connect = () => {
    const target = candidates[Math.min(candidateIndex, candidates.length - 1)];
    handlers.onConnecting?.(target);

    socket = new WebSocket(target);

    socket.addEventListener('open', () => {
      candidateIndex = 0;
      handlers.onOpen?.(socket, target);
    });

    socket.addEventListener('close', (event) => {
      handlers.onClose?.(event, target);

      if (manuallyClosed) {
        return;
      }

      if (!event.wasClean && candidateIndex < candidates.length - 1) {
        candidateIndex += 1;
        connect();
        return;
      }

      reconnectTimer = window.setTimeout(() => {
        candidateIndex = 0;
        connect();
      }, 1500);
    });

    socket.addEventListener('error', (event) => {
      handlers.onError?.(event, target);
    });

    socket.addEventListener('message', (event) => {
      try {
        handlers.onMessage?.(JSON.parse(event.data));
      } catch {
        handlers.onInvalidMessage?.(event.data);
      }
    });
  };

  connect();

  return {
    get readyState() {
      return socket?.readyState ?? WebSocket.CLOSED;
    },
    send(data) {
      socket?.send(data);
    },
    close() {
      manuallyClosed = true;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      socket?.close();
    },
  };
}

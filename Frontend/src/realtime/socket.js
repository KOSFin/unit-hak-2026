function normalizeSocketUrl(rawUrl, fallbackPath = '/ws') {
  if (rawUrl) {
    if (/^wss?:\/\//i.test(rawUrl)) {
      return rawUrl;
    }
    if (/^https?:\/\//i.test(rawUrl)) {
      const url = new URL(rawUrl);
      url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
      return url.toString();
    }
    if (rawUrl.startsWith('/')) {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${protocol}//${window.location.host}${rawUrl}`;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${rawUrl}`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${fallbackPath}`;
}

function withSocketPath(rawUrl, nextPath) {
  try {
    const url = new URL(rawUrl);
    url.pathname = nextPath;
    return url.toString();
  } catch {
    return rawUrl;
  }
}

function buildCandidateUrls() {
  const explicitUrl = import.meta.env.VITE_WS_URL;
  const normalizedExplicitUrl = explicitUrl ? normalizeSocketUrl(explicitUrl) : '';
  const explicitCandidates = normalizedExplicitUrl
    ? [normalizedExplicitUrl, withSocketPath(normalizedExplicitUrl, '/api/ws')]
    : [];
  const fallbackCandidates = [normalizeSocketUrl('', '/ws'), normalizeSocketUrl('', '/api/ws')];
  return [...new Set([...explicitCandidates, ...fallbackCandidates])];
}

export function createRealtimeSocket(handlers = {}) {
  const candidates = buildCandidateUrls();
  let socket = null;
  let candidateIndex = 0;
  let reconnectTimer = null;
  let manuallyClosed = false;
  let reconnectDelay = 1500;

  const scheduleReconnect = () => {
    reconnectTimer = window.setTimeout(() => {
      candidateIndex = 0;
      connect();
    }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 10000);
  };

  const connect = () => {
    const target = candidates[Math.min(candidateIndex, candidates.length - 1)];
    handlers.onConnecting?.(target);

    socket = new WebSocket(target);

    socket.addEventListener('open', () => {
      candidateIndex = 0;
      reconnectDelay = 1500;
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

      scheduleReconnect();
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

import { createContext, useContext, useEffect, useRef, useState } from 'react';

const WsContext = createContext(null);

export function WsProvider({ boardId, children }) {
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!boardId) return;
    const BASE_WS = import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}`;
    const token = 'valid-token'; // Replace with real auth token
    const ws = new WebSocket(`${BASE_WS}/ws/${boardId}?token=${token}`);

    ws.onmessage = (e) => {
      try { setLastEvent(JSON.parse(e.data)); }
      catch { /* ignore malformed */ }
    };
    ws.onerror = () => ws.close();
    wsRef.current = ws;

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [boardId]);

  return <WsContext.Provider value={lastEvent}>{children}</WsContext.Provider>;
}

export const useWsEvent = () => useContext(WsContext);

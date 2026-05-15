import { useEffect, useRef, useState } from 'react';
import { api } from './api/client.js';
import Sidebar from './components/Sidebar.jsx';
import { WsProvider } from './contexts/WsContext.jsx';
import BoardView from './views/BoardView.jsx';
import IncomingTasksView from './views/IncomingTasksView.jsx';
import NotificationsView from './views/NotificationsView.jsx';
import './index.css';

const LAYOUT = {
  display: 'flex',
};

const MAIN = {
  flex: 1,
  marginLeft: 'var(--sidebar-width)',
  minWidth: 0,
};

function App() {
  const [view, setView] = useState('board');
  const [boardId, setBoardId] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  // Bootstrap: get or create the default board
  useEffect(() => {
    api.getBoards()
      .then((boards) => {
        if (boards.length > 0) {
          setBoardId(boards[0].id);
        } else {
          return api.createBoard('My Board').then((b) => setBoardId(b.id));
        }
      })
      .catch(console.error);
  }, []);

  // Maintain WS connection status
  useEffect(() => {
    if (!boardId) return;
    const BASE_WS = import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}`;
    const ws = new WebSocket(`${BASE_WS}/ws/${boardId}?token=valid-token`);
    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => { setWsConnected(false); ws.close(); };
    wsRef.current = ws;
    return () => ws.close();
  }, [boardId]);

  const renderView = () => {
    switch (view) {
      case 'board':         return <BoardView boardId={boardId} wsConnected={wsConnected} />;
      case 'notifications': return <NotificationsView wsConnected={wsConnected} />;
      case 'incoming':      return <IncomingTasksView wsConnected={wsConnected} />;
      case 'automations':   return (
        <div style={{ paddingTop: 'var(--topbar-height)', padding: '80px 48px', color: 'var(--color-text-muted)' }}>
          <h2>Automations</h2>
          <p style={{ marginTop: 8 }}>Automation rules management coming soon.</p>
        </div>
      );
      default: return null;
    }
  };

  return (
    <WsProvider boardId={boardId}>
      <div style={LAYOUT}>
        <Sidebar view={view} onNav={setView} />
        <div style={MAIN} id="main-content">
          {renderView()}
        </div>
      </div>
    </WsProvider>
  );
}

export default App;

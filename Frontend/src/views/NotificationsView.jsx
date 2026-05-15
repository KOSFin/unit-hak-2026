import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Topbar from '../components/Topbar.jsx';
import s from './NotificationsView.module.css';

export default function NotificationsView({ wsConnected }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const load = async () => {
    try {
      const data = await api.getNotifications(unreadOnly ? { unread_only: true } : {});
      setItems(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { setLoading(true); load(); }, [unreadOnly]);

  const markRead = async (id) => {
    await api.markNotificationRead(id);
    setItems((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));
  };

  const unreadCount = items.filter((n) => !n.read).length;

  return (
    <>
      <Topbar
        title="Notifications"
        wsConnected={wsConnected}
        unreadCount={unreadCount}
      />
      <div className={s.container}>
        <div className={s.list}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
            <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} id="chk-unread-only" />
            Unread only
          </label>

          {loading && <p className={s.empty}>Loading…</p>}
          {!loading && items.length === 0 && <p className={s.empty}>No notifications.</p>}

          {items.map((n) => (
            <div key={n.id} id={`notif-${n.id}`} className={`${s.card}${!n.read ? ' ' + s.unread : ''}`}>
              <span className={`${s.iconDot}${n.read ? ' ' + s.read : ''}`} />
              <div className={s.content}>
                <p className={s.title}>{n.title}</p>
                <p className={s.message}>{n.message}</p>
              </div>
              <span className={s.time}>{new Date(n.created_at).toLocaleString()}</span>
              {!n.read && (
                <button id={`btn-mark-read-${n.id}`} className={s.markBtn} onClick={() => markRead(n.id)}>
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

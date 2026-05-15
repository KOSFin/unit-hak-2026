import { useEffect, useState } from 'react';
import { api } from '../api/client';
import Topbar from '../components/Topbar.jsx';
import s from './IncomingTasksView.module.css';

export default function IncomingTasksView({ wsConnected }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await api.getIncomingTasks();
      setItems(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const act = async (id, action) => {
    const fn = action === 'accept' ? api.acceptIncomingTask : api.rejectIncomingTask;
    const updated = await fn(id);
    setItems((prev) => prev.map((t) => t.id === id ? updated : t));
  };

  return (
    <>
      <Topbar title="Incoming Tasks" wsConnected={wsConnected} />
      <div className={s.container}>
        <div className={s.list}>
          {loading && <p className={s.empty}>Loading…</p>}
          {!loading && items.length === 0 && <p className={s.empty}>No incoming tasks.</p>}
          {items.map((t) => (
            <div key={t.id} id={`incoming-${t.id}`} className={s.card}>
              <div className={s.info}>
                <p className={s.extId}>#{t.external_id}</p>
                <p className={s.payload}>{JSON.stringify(t.raw_payload)}</p>
              </div>
              <span className={`${s.status} ${s[t.status]}`}>{t.status}</span>
              {t.status === 'PENDING' && (
                <div className={s.actions}>
                  <button id={`btn-accept-${t.id}`} className={s.btnAccept} onClick={() => act(t.id, 'accept')}>Accept</button>
                  <button id={`btn-reject-${t.id}`} className={s.btnReject} onClick={() => act(t.id, 'reject')}>Reject</button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './IncomingTasksPanel.module.css';

function getTone(status) {
  if (status === 'REJECTED') return 'danger';
  if (status === 'PROCESSED') return 'success';
  if (status === 'DUPLICATE') return 'warning';
  return 'neutral';
}

export default function IncomingTasksPanel({ items, pending, onSendDemoTask }) {
  return (
    <section className={styles.panel}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>API intake</p>
          <h2>Incoming tasks</h2>
        </div>
        <Button variant="secondary" onClick={onSendDemoTask} disabled={pending}>
          Send test task
        </Button>
      </div>

      <div className={styles.list}>
        {items.length === 0 ? <div className={styles.empty}>No incoming tasks yet.</div> : null}
        {items.map((item) => (
          <article key={item.id} className={styles.card}>
            <div className={styles.cardHeader}>
              <strong>{item.external_id}</strong>
              <Badge tone={getTone(item.status)}>{item.status}</Badge>
            </div>
            <pre className={styles.payload}>{JSON.stringify(item.raw_payload, null, 2)}</pre>
            {item.validation_error ? <p className={styles.error}>{item.validation_error}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}

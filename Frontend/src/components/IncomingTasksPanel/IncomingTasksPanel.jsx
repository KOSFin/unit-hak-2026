import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './IncomingTasksPanel.module.css';

function getTone(status) {
  if (status === 'REJECTED') return 'danger';
  if (status === 'PROCESSED') return 'success';
  if (status === 'DUPLICATE') return 'warning';
  return 'neutral';
}

function getStatusLabel(status, language) {
  const keyMap = {
    RECEIVED: 'received',
    VALIDATED: 'validated',
    REJECTED: 'rejected',
    PROCESSED: 'processed',
    DUPLICATE: 'duplicate',
  };
  return t(keyMap[status] || status, language);
}

export default function IncomingTasksPanel({ items, pending, onSendDemoTask }) {
  const { language } = useLocale();
  return (
    <section className={styles.panel}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>{t('apiIntake', language)}</p>
          <h2>{t('incomingTasks', language)}</h2>
        </div>
        <Button variant="secondary" onClick={onSendDemoTask} disabled={pending}>
          {t('sendTestTask', language)}
        </Button>
      </div>

      <div className={styles.list}>
        {items.length === 0 ? <div className={styles.empty}>{t('noIncomingTasksYet', language)}</div> : null}
        {items.map((item) => (
          <article key={item.id} className={styles.card}>
            <div className={styles.cardHeader}>
              <strong>{item.external_id}</strong>
              <Badge tone={getTone(item.status)}>{getStatusLabel(item.status, language)}</Badge>
            </div>
            <pre className={styles.payload}>{JSON.stringify(item.raw_payload, null, 2)}</pre>
            {item.validation_error ? <p className={styles.error}>{item.validation_error}</p> : null}
          </article>
        ))}
      </div>
    </section>
  );
}

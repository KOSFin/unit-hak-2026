import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './NotificationsPanel.module.css';

export default function NotificationsPanel({
  notifications,
  pending,
  onMarkRead,
  onMarkAllRead,
}) {
  const { language } = useLocale();
  const formatTimestamp = (value) =>
    new Date(value).toLocaleString(language === 'ru' ? 'ru-RU' : 'en-US', {
      dateStyle: 'short',
      timeStyle: 'short',
    });
  const unreadCount = notifications.filter((notification) => !notification.read).length;

  return (
    <section className={styles.panel}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>{t('realtimeInbox', language)}</p>
          <h2>{t('notifications', language)}</h2>
        </div>
        <Badge tone={unreadCount > 0 ? 'accent' : 'neutral'}>{unreadCount} {t('unread', language)}</Badge>
      </div>

      <Button variant="secondary" block onClick={onMarkAllRead} disabled={pending || unreadCount === 0}>
        {t('markAllAsRead', language)}
      </Button>

      <div className={styles.list}>
        {notifications.length === 0 ? <div className={styles.empty}>{t('noNotificationsYet', language)}</div> : null}
        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`${styles.card} ${notification.read ? styles.read : styles.unread}`}
          >
            <div className={styles.cardHeader}>
              <h3>{notification.title}</h3>
              <span>{formatTimestamp(notification.created_at)}</span>
            </div>
            <p className={styles.message}>{notification.message}</p>
            {!notification.read ? (
              <Button variant="ghost" size="sm" onClick={() => onMarkRead(notification.id)}>
                {t('markRead', language)}
              </Button>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

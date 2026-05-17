import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './NotificationsMenu.module.css';

function formatTimestamp(value, language) {
  return new Date(value).toLocaleString(language === 'ru' ? 'ru-RU' : 'en-US', {
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

export default function NotificationsMenu({
  notifications,
  pending,
  onMarkRead,
  onMarkAllRead,
  className = '',
}) {
  const { language } = useLocale();
  const unreadCount = notifications.filter((notification) => !notification.read).length;

  return (
    <section className={`${styles.menu} ${className}`.trim()} role="dialog" aria-label={t('notifications', language)}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>{t('realtimeInbox', language)}</p>
          <h3>{t('notifications', language)}</h3>
        </div>
        <Badge tone={unreadCount > 0 ? 'accent' : 'neutral'}>{unreadCount}</Badge>
      </div>

      <Button variant="ghost" size="sm" block onClick={onMarkAllRead} disabled={pending || unreadCount === 0}>
        {t('markAllRead', language)}
      </Button>

      <div className={styles.list}>
        {notifications.length === 0 ? <div className={styles.empty}>{t('noNotificationsYet', language)}</div> : null}
        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`${styles.card} ${notification.read ? styles.read : styles.unread}`}
          >
            <div className={styles.cardHeader}>
              <h4>{notification.title}</h4>
              <span>{formatTimestamp(notification.created_at, language)}</span>
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

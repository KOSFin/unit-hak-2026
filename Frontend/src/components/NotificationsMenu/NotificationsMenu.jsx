import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './NotificationsMenu.module.css';

function formatTimestamp(value) {
  return new Date(value).toLocaleString('ru-RU', {
    dateStyle: 'short',
    timeStyle: 'short',
  });
}

export default function NotificationsMenu({
  notifications,
  pending,
  onMarkRead,
  onMarkAllRead,
}) {
  const unreadCount = notifications.filter((notification) => !notification.read).length;

  return (
    <section className={styles.menu} role="dialog" aria-label="Notifications">
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>Realtime inbox</p>
          <h3>Notifications</h3>
        </div>
        <Badge tone={unreadCount > 0 ? 'accent' : 'neutral'}>{unreadCount}</Badge>
      </div>

      <Button variant="ghost" size="sm" block onClick={onMarkAllRead} disabled={pending || unreadCount === 0}>
        Mark all read
      </Button>

      <div className={styles.list}>
        {notifications.length === 0 ? <div className={styles.empty}>No notifications yet.</div> : null}
        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`${styles.card} ${notification.read ? styles.read : styles.unread}`}
          >
            <div className={styles.cardHeader}>
              <h4>{notification.title}</h4>
              <span>{formatTimestamp(notification.created_at)}</span>
            </div>
            <p className={styles.message}>{notification.message}</p>
            {!notification.read ? (
              <Button variant="ghost" size="sm" onClick={() => onMarkRead(notification.id)}>
                Mark read
              </Button>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

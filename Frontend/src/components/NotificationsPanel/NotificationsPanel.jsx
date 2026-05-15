import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './NotificationsPanel.module.css';

export default function NotificationsPanel({
  notifications,
  pending,
  onMarkRead,
  onMarkAllRead,
}) {
  const unreadCount = notifications.filter((notification) => !notification.read).length;

  return (
    <section className={styles.panel}>
      <div className={styles.header}>
        <div>
          <p className={styles.kicker}>Realtime inbox</p>
          <h2>Notifications</h2>
        </div>
        <Badge tone={unreadCount > 0 ? 'accent' : 'neutral'}>{unreadCount} unread</Badge>
      </div>

      <Button variant="secondary" block onClick={onMarkAllRead} disabled={pending || unreadCount === 0}>
        Mark all as read
      </Button>

      <div className={styles.list}>
        {notifications.length === 0 ? <div className={styles.empty}>No notifications yet.</div> : null}
        {notifications.map((notification) => (
          <article
            key={notification.id}
            className={`${styles.card} ${notification.read ? styles.read : styles.unread}`}
          >
            <div className={styles.cardHeader}>
              <h3>{notification.title}</h3>
              <span>{new Date(notification.created_at).toLocaleString()}</span>
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

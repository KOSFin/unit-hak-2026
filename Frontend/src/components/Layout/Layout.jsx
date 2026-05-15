import { useEffect, useRef } from 'react';

import Button from '../Ui/Button';
import NotificationsMenu from '../NotificationsMenu/NotificationsMenu';
import styles from './Layout.module.css';

export default function Layout({
  onCreateTask,
  onOpenAdmin,
  boardName,
  children,
  notifications,
  notificationsOpen,
  pending,
  onToggleNotifications,
  onCloseNotifications,
  onMarkNotificationRead,
  onMarkAllNotificationsRead,
}) {
  const unreadCount = notifications.filter((notification) => !notification.read).length;

  const menuRef = useRef(null);

  useEffect(() => {
    if (!notificationsOpen) {
      return undefined;
    }

    const handleOutsideClick = (event) => {
      if (!menuRef.current || menuRef.current.contains(event.target)) {
        return;
      }
      onCloseNotifications();
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onCloseNotifications();
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [notificationsOpen, onCloseNotifications]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.identity}>
          <div className={styles.logo}>FB</div>
          <div>
            <p className={styles.eyebrow}>FlowBoard</p>
            <h1 className={styles.title}>{boardName ?? 'Event-driven kanban board'}</h1>
          </div>
        </div>

        <div className={styles.actions}>
          <div className={styles.menu} ref={menuRef}>
            <button
              className={`${styles.notificationsButton} ${notificationsOpen ? styles.notificationsActive : ''}`}
              onClick={onToggleNotifications}
              type="button"
            >
              Notifications
              <span className={styles.notificationsBadge}>{unreadCount}</span>
            </button>
            {notificationsOpen ? (
              <NotificationsMenu
                notifications={notifications}
                pending={pending}
                onMarkRead={onMarkNotificationRead}
                onMarkAllRead={onMarkAllNotificationsRead}
              />
            ) : null}
          </div>
          <Button variant="secondary" size="sm" onClick={onOpenAdmin}>
            Admin
          </Button>
          <Button size="sm" onClick={onCreateTask}>
            Create Task
          </Button>
        </div>
      </header>

      <main className={styles.main}>{children}</main>
    </div>
  );
}

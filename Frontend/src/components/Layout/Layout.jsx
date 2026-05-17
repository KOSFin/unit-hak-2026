import { useEffect, useRef, useState } from 'react';

import Button from '../Ui/Button';
import NotificationsMenu from '../NotificationsMenu/NotificationsMenu';
import ProfileModal from '../ProfileModal/ProfileModal';
import ShareModal from '../ShareModal/ShareModal';
import styles from './Layout.module.css';

export default function Layout({
  board,
  identity,
  onUpdateIdentity,
  onlineUsers = [],
  onCreateTask,
  onOpenAdmin,
  onToggleEventFlow,
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
  const [profileOpen, setProfileOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);

  useEffect(() => {
    if (!notificationsOpen) return;
    const handleOutsideClick = (event) => {
      if (!menuRef.current || menuRef.current.contains(event.target)) return;
      onCloseNotifications();
    };
    const handleEscape = (event) => {
      if (event.key === 'Escape') onCloseNotifications();
    };
    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [notificationsOpen, onCloseNotifications]);

  const displayedUsers = onlineUsers.slice(0, 3);
  const extraUsers = Math.max(0, onlineUsers.length - 3);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.identity}>
          {board?.image_path ? (
            <img src={board.image_path} alt="Board Logo" className={styles.logoImg} />
          ) : (
            <div className={styles.logo}>FB</div>
          )}
          <div>
            <h1 className={styles.title}>{board?.name ?? 'FlowBoard'}</h1>
            <p className={styles.eyebrow}>
              Temporary board &middot; expires after {board?.expires_after_days ?? 3} inactive days
            </p>
          </div>
        </div>

        <div className={styles.actions}>
          {onlineUsers.length > 0 && (
             <div className={styles.onlineGroup}>
               {displayedUsers.map(user => (
                 <div 
                   key={user.guest_id} 
                   className={styles.onlineAvatar} 
                   style={{ backgroundColor: user.color, backgroundImage: user.avatar_url ? `url(${user.avatar_url})` : 'none', backgroundSize: 'cover' }}
                   title={user.display_name}
                 >
                   {!user.avatar_url && user.display_name.charAt(0).toUpperCase()}
                 </div>
               ))}
               {extraUsers > 0 && (
                 <div className={styles.onlineExtra}>+{extraUsers}</div>
               )}
             </div>
          )}
          
          <Button variant="ghost" size="sm" onClick={() => setShareOpen(true)} className={styles.iconBtn}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
          </Button>

          <Button variant="ghost" size="sm" onClick={onToggleEventFlow} className={styles.iconBtn}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
          </Button>

          <div className={styles.menu} ref={menuRef}>
            <Button
              variant="ghost"
              size="sm"
              className={`${styles.iconBtn} ${styles.notifBtn}`}
              onClick={onToggleNotifications}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
              {unreadCount > 0 && <span className={styles.notificationsBadge}>{unreadCount}</span>}
            </Button>
            {notificationsOpen ? (
              <NotificationsMenu
                notifications={notifications}
                pending={pending}
                onMarkRead={onMarkNotificationRead}
                onMarkAllRead={onMarkAllNotificationsRead}
              />
            ) : null}
          </div>
          
          <Button variant="secondary" size="sm" onClick={onOpenAdmin}>Admin</Button>
          <Button size="sm" onClick={onCreateTask}>Create Task</Button>
          
          <div 
             className={styles.profileBtn} 
             style={{ backgroundColor: identity?.color, backgroundImage: identity?.avatarUrl ? `url(${identity.avatarUrl})` : 'none', backgroundSize: 'cover' }}
             onClick={() => setProfileOpen(true)}
          >
             {!identity?.avatarUrl && identity?.displayName?.charAt(0).toUpperCase()}
          </div>
        </div>
      </header>

      <main className={styles.main}>{children}</main>

      {profileOpen && (
        <ProfileModal 
          identity={identity} 
          onClose={() => setProfileOpen(false)} 
          onUpdate={(updated) => {
            onUpdateIdentity(updated);
            setProfileOpen(false);
          }}
        />
      )}
      
      {shareOpen && (
        <ShareModal board={board} onClose={() => setShareOpen(false)} />
      )}
    </div>
  );
}

import { useEffect, useMemo, useRef, useState } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Button from '../Ui/Button';
import NotificationsMenu from '../NotificationsMenu/NotificationsMenu';
import ProfileModal from '../ProfileModal/ProfileModal';
import ShareModal from '../ShareModal/ShareModal';
import styles from './Layout.module.css';

const DAY_IN_MS = 24 * 60 * 60 * 1000;
const HOUR_IN_MS = 60 * 60 * 1000;
const MINUTE_IN_MS = 60 * 1000;

function getInitial(name = 'Guest') {
  return name.trim().charAt(0).toUpperCase() || 'G';
}

function formatAbsoluteDate(value) {
  if (!value) {
    return 'No activity yet';
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function formatDuration(ms) {
  if (!Number.isFinite(ms)) {
    return 'Unknown';
  }

  const absMs = Math.abs(ms);
  const days = Math.floor(absMs / DAY_IN_MS);
  const hours = Math.floor((absMs % DAY_IN_MS) / HOUR_IN_MS);
  const minutes = Math.max(1, Math.floor((absMs % HOUR_IN_MS) / MINUTE_IN_MS));

  if (days > 0) {
    return `${days}d ${hours}h`;
  }

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }

  return `${minutes}m`;
}

function getLifecycleState(timeLeftMs) {
  if (!Number.isFinite(timeLeftMs) || timeLeftMs <= 0) {
    return {
      label: 'Expiring now',
      toneClassName: styles.lifecycleDanger,
      helper: 'The board is at the end of its inactivity window.',
    };
  }

  if (timeLeftMs <= DAY_IN_MS) {
    return {
      label: 'Expires within a day',
      toneClassName: styles.lifecycleWarning,
      helper: 'A fresh task update will extend the board lifetime.',
    };
  }

  return {
    label: 'Healthy workspace',
    toneClassName: styles.lifecycleSuccess,
    helper: 'The board still has plenty of runway left.',
  };
}

function buildLifecycleSnapshot(board, now) {
  if (!board?.last_activity_at) {
    return {
      lastActivityLabel: 'No activity yet',
      expiresAtLabel: 'Waiting for first action',
      retentionLabel: `${board?.expires_after_days ?? 3} inactive days`,
      timeLeftLabel: 'Starts after first task action',
      state: getLifecycleState(Number.NaN),
    };
  }

  const lastActivityMs = new Date(board.last_activity_at).getTime();
  const expiresAtMs = lastActivityMs + (board.expires_after_days ?? 3) * DAY_IN_MS;
  const timeLeftMs = expiresAtMs - now;

  return {
    lastActivityLabel: formatAbsoluteDate(board.last_activity_at),
    expiresAtLabel: formatAbsoluteDate(expiresAtMs),
    retentionLabel: `${board.expires_after_days ?? 3} inactive days`,
    timeLeftLabel:
      timeLeftMs > 0 ? `${formatDuration(timeLeftMs)} left` : `${formatDuration(timeLeftMs)} overdue`,
    state: getLifecycleState(timeLeftMs),
  };
}

function ToolbarIcon({ children }) {
  return <span className={styles.toolbarIcon}>{children}</span>;
}

export default function Layout({
  board,
  identity,
  onUpdateIdentity,
  onlineUsers = [],
  realtimeStatus = 'idle',
  onCreateTask,
  onOpenAdmin,
  onToggleEventFlow,
  children,
  notifications,
  notificationsOpen,
  pending,
  onUpdateBoardImage,
  onToggleNotifications,
  onCloseNotifications,
  onMarkNotificationRead,
  onMarkAllNotificationsRead,
  mainClassName = '',
  columns = [],
  searchQuery = '',
  onSearchQueryChange,
  columnFilter = 'ALL',
  onColumnFilterChange,
  priorityFilter = 'ALL',
  onPriorityFilterChange,
  sortMode = 'BOARD_ORDER',
  onSortModeChange,
  onResetTaskView,
  visibleTaskCount = 0,
  // eslint-disable-next-line no-unused-vars
  totalTaskCount = 0,
  taskViewActive = false,
}) {
  const { language } = useLocale();
  const unreadCount = notifications.filter((notification) => !notification.read).length;
  const menuRef = useRef(null);
  const onlineRef = useRef(null);
  const boardImageInputRef = useRef(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [onlineOpen, setOnlineOpen] = useState(false);
  const [boardInfoOpen, setBoardInfoOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setNow(Date.now());
    }, 60_000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!notificationsOpen && !onlineOpen) {
      return undefined;
    }

    const handleOutsideClick = (event) => {
      if (!menuRef.current || menuRef.current.contains(event.target)) {
        return;
      }
      if (onlineRef.current && onlineRef.current.contains(event.target)) {
        return;
      }
      onCloseNotifications();
      setOnlineOpen(false);
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onCloseNotifications();
        setOnlineOpen(false);
        setBoardInfoOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [notificationsOpen, onlineOpen, onCloseNotifications]);

  const lifecycle = useMemo(() => buildLifecycleSnapshot(board, now), [board, now]);

  const displayedUsers = onlineUsers.slice(0, 3);
  const extraUsers = Math.max(0, onlineUsers.length - 3);
  const showOnlineControl = onlineUsers.length > 0 || realtimeStatus !== 'connected';
  const realtimeLabel =
    realtimeStatus === 'connected'
      ? `${onlineUsers.length} online`
      : realtimeStatus === 'connecting'
        ? 'Connecting…'
        : realtimeStatus === 'error'
          ? 'Realtime offline'
          : 'Disconnected';

  return (
    <div className={styles.page}>
      <header className={styles.topHeader}>
        <div className={styles.identityCluster}>
          <button
            type="button"
            className={styles.boardLogoButton}
            onClick={() => boardImageInputRef.current?.click()}
            aria-label="Change board image"
          >
            {board?.image_path ? (
              <img src={board.image_path} alt="Board Logo" className={styles.logoImg} />
            ) : (
              <div className={styles.logo}>{getInitial(board?.name || 'FlowBoard')}</div>
            )}
          </button>
          <input
            ref={boardImageInputRef}
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(event) => onUpdateBoardImage?.(event.target.files?.[0] ?? null, event.currentTarget)}
          />

          <div className={styles.titleBlock}>
            <p className={styles.serviceName}>FlowBoard</p>
            <div className={styles.boardTitleRow}>
              <h1 className={styles.boardTitle}>{board?.name ?? 'Untitled board'}</h1>

              <div
                className={styles.infoWrap}
                onMouseEnter={() => setBoardInfoOpen(true)}
                onMouseLeave={() => setBoardInfoOpen(false)}
                onFocus={() => setBoardInfoOpen(true)}
                onBlur={(event) => {
                  if (!event.currentTarget.contains(event.relatedTarget)) {
                    setBoardInfoOpen(false);
                  }
                }}
              >
                <button
                  type="button"
                  className={styles.infoButton}
                  aria-label="Board lifetime details"
                  aria-expanded={boardInfoOpen}
                >
                  !
                </button>

                {boardInfoOpen ? (
                  <div className={styles.infoCard} role="note" aria-label="Board lifetime details">
                    <div className={styles.infoHeader}>
                      <div>
                        <p className={styles.infoEyebrow}>Board lifecycle</p>
                        <h2>Temporary workspace status</h2>
                      </div>
                      <span className={`${styles.lifecycleBadge} ${lifecycle.state.toneClassName}`}>
                        {lifecycle.state.label}
                      </span>
                    </div>

                    <div className={styles.infoGrid}>
                      <article className={styles.infoStatCard}>
                        <span>Last activity</span>
                        <strong>{lifecycle.lastActivityLabel}</strong>
                        <p>Most recent board-changing action across tasks, rules, and queue events.</p>
                      </article>

                      <article className={styles.infoStatCard}>
                        <span>Retention window</span>
                        <strong>{lifecycle.retentionLabel}</strong>
                        <p>Every fresh task update refreshes the inactivity timer.</p>
                      </article>

                      <article className={styles.infoStatCard}>
                        <span>Time remaining</span>
                        <strong>{lifecycle.timeLeftLabel}</strong>
                        <p>{lifecycle.state.helper}</p>
                      </article>
                    </div>

                    <div className={styles.infoFooter}>
                      <div className={styles.infoFooterHeader}>
                        <span>Next cleanup checkpoint</span>
                        <strong>{lifecycle.expiresAtLabel}</strong>
                      </div>

                      <div className={styles.lockedRetention}>
                        <div className={styles.lockedRetentionCopy}>
                          <span>Retention preset</span>
                          <p>Long-lived boards will unlock once account workspaces land.</p>
                        </div>

                        <button type="button" className={styles.lockedSelect} disabled>
                          <span>{board?.expires_after_days ?? 3} days MVP board</span>
                          <span className={styles.lockedSelectMeta}>Auth soon</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          {showOnlineControl ? (
            <div className={styles.onlineWrap} ref={onlineRef}>
              <button
                type="button"
                className={styles.onlineGroup}
                aria-label={realtimeLabel}
                onClick={() => setOnlineOpen((current) => !current)}
              >
                <span
                  className={`${styles.realtimeDot} ${styles[`status${realtimeStatus[0]?.toUpperCase?.() + realtimeStatus.slice(1)}`] || ''}`}
                ></span>
                <div className={styles.onlineLabelBlock}>
                  <span className={styles.onlineLabel}>Live now</span>
                  <span className={styles.onlineValue}>{realtimeLabel}</span>
                </div>
                <div className={styles.onlineAvatars}>
                  {displayedUsers.map((user) => (
                    <div
                      key={user.guest_id}
                      className={styles.onlineAvatar}
                      style={{
                        backgroundColor: user.color,
                        backgroundImage: user.avatar_url ? `url(${user.avatar_url})` : 'none',
                        backgroundSize: 'cover',
                      }}
                      title={user.display_name}
                    >
                      {!user.avatar_url && getInitial(user.display_name)}
                    </div>
                  ))}
                  {displayedUsers.length === 0 ? (
                    <span className={styles.onlineFallback}>Waiting for collaborators</span>
                  ) : null}
                  {extraUsers > 0 ? <div className={styles.onlineExtra}>+{extraUsers}</div> : null}
                </div>
              </button>

              {onlineOpen ? (
                <div className={styles.onlineDropdown}>
                  <div className={styles.onlineDropdownHeader}>
                    <strong>{realtimeLabel}</strong>
                  </div>
                  <div className={styles.onlineList}>
                    {onlineUsers.length === 0 ? (
                      <div className={styles.onlineEmpty}>
                        We&apos;ll show live collaborators here as soon as the realtime channel connects.
                      </div>
                    ) : null}
                    {onlineUsers.map((user) => (
                      <div key={user.guest_id} className={styles.onlineRow}>
                        <div
                          className={styles.onlineAvatarLarge}
                          style={{
                            backgroundColor: user.color,
                            backgroundImage: user.avatar_url ? `url(${user.avatar_url})` : 'none',
                            backgroundSize: 'cover',
                          }}
                        >
                          {!user.avatar_url && getInitial(user.display_name)}
                        </div>
                        <div>
                          <div className={styles.onlineName}>{user.display_name}</div>
                          <div className={styles.onlineMeta}>
                            {user.guest_id === identity?.id ? 'You' : 'Guest collaborator'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          <Button variant="ghost" size="sm" onClick={onToggleEventFlow} className={styles.iconBtn}>
            <ToolbarIcon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </ToolbarIcon>
            <span className="sr-only">Activity</span>
          </Button>

          <Button variant="ghost" size="sm" onClick={() => setShareOpen(true)} className={styles.iconBtn}>
            <ToolbarIcon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 13a5 5 0 0 0 7.07 0l3.54-3.54a5 5 0 0 0-7.07-7.07L12.5 4.43" />
                <path d="M14 11a5 5 0 0 0-7.07 0L3.4 14.54a5 5 0 0 0 7.07 7.07L11.5 19.57" />
              </svg>
            </ToolbarIcon>
            <span className="sr-only">Share</span>
          </Button>

          <div className={styles.menu} ref={menuRef}>
            <Button
              variant="ghost"
              size="sm"
              className={`${styles.iconBtn} ${styles.notifBtn}`}
              onClick={onToggleNotifications}
            >
              <ToolbarIcon>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                  <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
              </ToolbarIcon>
              {unreadCount > 0 ? <span className={styles.notificationsBadge}>{unreadCount}</span> : null}
              <span className="sr-only">Notifications</span>
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

          <Button variant="secondary" size="sm" onClick={onOpenAdmin} className={styles.adminButton}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82L4.21 7.2a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            <span>Admin</span>
          </Button>

          <button
            type="button"
            className={styles.profileBtn}
            onClick={() => setProfileOpen(true)}
            style={{
              backgroundColor: identity?.color,
              backgroundImage: identity?.avatarUrl ? `url(${identity.avatarUrl})` : 'none',
              backgroundSize: 'cover',
            }}
            aria-label="Open profile"
          >
            {!identity?.avatarUrl && getInitial(identity?.displayName)}
          </button>
        </div>
      </header>

      <div className={styles.toolbarDock}>
        <section className={styles.toolbar} aria-label="Task search and filters">
          <label className={styles.searchField}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              value={searchQuery}
              onChange={(event) => onSearchQueryChange?.(event.target.value)}
              placeholder={t('search', language)}
            />
            {searchQuery ? (
              <button
                type="button"
                className={styles.clearSearch}
                onClick={() => onSearchQueryChange?.('')}
                aria-label={t('clearSearch', language)}
                title={t('clearSearch', language)}
              >
                ×
              </button>
            ) : null}
            {searchQuery && (
              <span className={styles.searchCount}>
                {visibleTaskCount}
              </span>
            )}
          </label>

          <button
            type="button"
            className={`${styles.toolbarChip} ${filtersOpen ? styles.toolbarChipActive : ''} ${taskViewActive ? styles.toolbarChipWarning : ''}`}
            onClick={() => setFiltersOpen((current) => !current)}
            title={taskViewActive ? t('dragPausedWarning', language) : ''}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
            <span>{t('filters', language)}</span>
            {taskViewActive && <span className={styles.chipBadge}>!</span>}
          </button>

          {filtersOpen ? (
            <div className={styles.filterPanel}>
              <label className={styles.compactField}>
                <span>{t('columnFilter', language)}</span>
                <select value={columnFilter} onChange={(event) => onColumnFilterChange?.(event.target.value)}>
                  <option value="ALL">{t('allColumns', language)}</option>
                  {columns.map((column) => (
                    <option key={column.id} value={column.id}>
                      {column.title}
                    </option>
                  ))}
                </select>
              </label>

              <label className={styles.compactField}>
                <span>{t('priorityFilter', language)}</span>
                <select
                  value={priorityFilter}
                  onChange={(event) => onPriorityFilterChange?.(event.target.value)}
                >
                  <option value="ALL">{t('anyPriority', language)}</option>
                  <option value="CRITICAL">{t('critical', language)}</option>
                  <option value="HIGH">{t('high', language)}</option>
                  <option value="MEDIUM">{t('medium', language)}</option>
                  <option value="LOW">{t('low', language)}</option>
                </select>
              </label>

              <label className={styles.compactField}>
                <span>{t('sortBy', language)}</span>
                <select value={sortMode} onChange={(event) => onSortModeChange?.(event.target.value)}>
                  <option value="BOARD_ORDER">{t('boardOrder', language)}</option>
                  <option value="UPDATED_DESC">{t('recentlyUpdated', language)}</option>
                  <option value="PRIORITY_DESC">{t('priorityFirst', language)}</option>
                  <option value="DEADLINE_ASC">{t('nearestDeadline', language)}</option>
                  <option value="TITLE_ASC">{t('titleAZ', language)}</option>
                </select>
              </label>

              {taskViewActive && (
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={onResetTaskView}
                  className={styles.resetButton}
                >
                  {t('resetView', language)}
                </Button>
              )}
            </div>
          ) : null}

          <Button size="sm" onClick={onCreateTask} className={styles.createTaskButton}>
            {t('createTask', language)}
          </Button>
        </section>
      </div>

      <main className={`${styles.main} ${mainClassName}`.trim()}>{children}</main>

      {profileOpen ? (
        <ProfileModal
          identity={identity}
          onClose={() => setProfileOpen(false)}
          onUpdate={(updated) => {
            onUpdateIdentity(updated);
            setProfileOpen(false);
          }}
        />
      ) : null}

      {shareOpen ? <ShareModal board={board} onClose={() => setShareOpen(false)} /> : null}
    </div>
  );
}

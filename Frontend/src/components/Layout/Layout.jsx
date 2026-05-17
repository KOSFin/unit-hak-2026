import { useEffect, useMemo, useRef, useState } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { getAvatarSurfaceStyle, getBoardCoverStyle } from '../../utils/imagePlaceholders';
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

function formatAbsoluteDate(value, language) {
  if (!value) {
    return t('noActivityYet', language);
  }

  return new Intl.DateTimeFormat(language === 'ru' ? 'ru-RU' : 'en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function formatDuration(ms, language) {
  if (!Number.isFinite(ms)) {
    return t('unknown', language);
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

function getLifecycleState(timeLeftMs, language) {
  if (!Number.isFinite(timeLeftMs) || timeLeftMs <= 0) {
    return {
      label: t('expiringNow', language),
      toneClassName: styles.lifecycleDanger,
      helper: t('boardAtEndOfInactivityWindow', language),
    };
  }

  if (timeLeftMs <= DAY_IN_MS) {
    return {
      label: t('expiresWithinDay', language),
      toneClassName: styles.lifecycleWarning,
      helper: t('freshTaskExtendsLifetime', language),
    };
  }

  return {
    label: t('healthyWorkspace', language),
    toneClassName: styles.lifecycleSuccess,
    helper: t('plentyOfRunwayLeft', language),
  };
}

function buildLifecycleSnapshot(board, now, language) {
  if (!board?.last_activity_at) {
    return {
      lastActivityLabel: t('noActivityYet', language),
      expiresAtLabel: t('waitingForFirstAction', language),
      retentionLabel: `${board?.expires_after_days ?? 3} ${t('daysLeft', language)}`,
      timeLeftLabel: t('startsAfterFirstTaskAction', language),
      state: getLifecycleState(Number.NaN, language),
    };
  }

  const lastActivityMs = new Date(board.last_activity_at).getTime();
  const expiresAtMs = lastActivityMs + (board.expires_after_days ?? 3) * DAY_IN_MS;
  const timeLeftMs = expiresAtMs - now;

  return {
    lastActivityLabel: formatAbsoluteDate(board.last_activity_at, language),
    expiresAtLabel: formatAbsoluteDate(expiresAtMs, language),
    retentionLabel: `${board.expires_after_days ?? 3} ${t('daysLeft', language)}`,
    timeLeftLabel:
      timeLeftMs > 0
        ? `${formatDuration(timeLeftMs, language)} ${t('leftSuffix', language)}`
        : `${formatDuration(timeLeftMs, language)} ${t('overdueSuffix', language)}`,
    state: getLifecycleState(timeLeftMs, language),
  };
}

function ToolbarIcon({ children }) {
  return <span className={styles.toolbarIcon}>{children}</span>;
}

function OnlineAvatarStack({ users, extraCount, language, size = 'md' }) {
  if (users.length === 0) {
    return <span className={styles.onlineFallback}>{t('waitingForCollaborators', language)}</span>;
  }

  return (
    <div className={`${styles.onlineAvatars} ${size === 'sm' ? styles.onlineAvatarsSmall : ''}`} aria-hidden="true">
      {users.map((user) => (
        <div
          key={user.guest_id}
          className={styles.onlineAvatar}
          style={getAvatarSurfaceStyle(user.avatar_url, user.color)}
          title={user.display_name}
        >
          {!user.avatar_url && getInitial(user.display_name)}
        </div>
      ))}
      {extraCount > 0 ? <div className={styles.onlineExtra}>+{extraCount}</div> : null}
    </div>
  );
}

function getRetentionPresetOptions(language) {
  return [
    { value: 3, label: language === 'ru' ? '3 дня' : '3 days', locked: false },
    { value: 7, label: language === 'ru' ? '7 дней' : '7 days', locked: true },
    { value: 30, label: language === 'ru' ? '30 дней' : '30 days', locked: true },
    { value: 365, label: language === 'ru' ? '1 год' : '1 year', locked: true },
  ];
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
  canManageBoard = true,
}) {
  const { language } = useLocale();
  const unreadCount = notifications.filter((notification) => !notification.read).length;
  const menuRef = useRef(null);
  const onlineRef = useRef(null);
  const boardInfoRef = useRef(null);
  const filtersRef = useRef(null);
  const boardImageInputRef = useRef(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [onlineOpen, setOnlineOpen] = useState(false);
  const [boardInfoOpen, setBoardInfoOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setNow(Date.now());
    }, 60_000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (!notificationsOpen && !onlineOpen && !boardInfoOpen && !filtersOpen && !mobileMenuOpen) {
      return undefined;
    }

    const handleOutsideClick = (event) => {
      if (menuRef.current?.contains(event.target)) {
        return;
      }
      if (onlineRef.current?.contains(event.target)) {
        return;
      }
      if (boardInfoRef.current?.contains(event.target)) {
        return;
      }
      if (filtersRef.current?.contains(event.target)) {
        return;
      }
      if (event.target.closest?.('[data-notifications-menu="true"]')) {
        return;
      }
      if (event.target.closest?.(`.${styles.mobileMenuPanel}`) || event.target.closest?.(`.${styles.mobileMenuButton}`)) {
        return;
      }
      onCloseNotifications();
      setOnlineOpen(false);
      setBoardInfoOpen(false);
      setFiltersOpen(false);
      setMobileMenuOpen(false);
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onCloseNotifications();
        setOnlineOpen(false);
        setBoardInfoOpen(false);
        setFiltersOpen(false);
        setMobileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [boardInfoOpen, filtersOpen, mobileMenuOpen, notificationsOpen, onlineOpen, onCloseNotifications]);

  const lifecycle = useMemo(() => buildLifecycleSnapshot(board, now, language), [board, now, language]);
  const retentionOptions = useMemo(() => getRetentionPresetOptions(language), [language]);

  const displayedUsers = onlineUsers.slice(0, 2);
  const extraUsers = Math.max(0, onlineUsers.length - 2);
  const showOnlineControl = onlineUsers.length > 0 || realtimeStatus !== 'connected';
  const realtimeLabel =
    realtimeStatus === 'connected'
      ? `${onlineUsers.length} ${t('online', language).toLowerCase()}`
      : realtimeStatus === 'connecting'
        ? t('connecting', language)
        : realtimeStatus === 'error'
          ? t('realtimeOffline', language)
          : t('disconnected', language);

  return (
    <div className={styles.page}>
      <header className={styles.topHeader}>
        <div className={styles.identityCluster}>
          <button
            type="button"
            className={styles.boardLogoButton}
            onClick={() => boardImageInputRef.current?.click()}
            aria-label={t('changeBoardImage', language)}
          >
            <div
              className={`${styles.logo} ${styles.logoImg}`}
              style={getBoardCoverStyle(board?.image_path)}
              aria-hidden="true"
            />
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
              <h1 className={styles.boardTitle}>{board?.name ?? t('untitledBoard', language)}</h1>

              <div className={styles.infoWrap} ref={boardInfoRef}>
                <button
                  type="button"
                  className={styles.infoButton}
                  aria-label={t('boardLifetimeDetails', language)}
                  aria-expanded={boardInfoOpen}
                  onClick={() => setBoardInfoOpen((current) => !current)}
                >
                  i
                </button>

                {boardInfoOpen ? (
                  <div className={styles.infoCard} role="note" aria-label={t('boardLifetimeDetails', language)}>
                    <div className={styles.infoHeader}>
                      <div>
                          <p className={styles.infoEyebrow}>{t('boardLifecycle', language)}</p>
                        <h2>{t('temporaryWorkspaceStatus', language)}</h2>
                      </div>
                      <span className={`${styles.lifecycleBadge} ${lifecycle.state.toneClassName}`}>
                        {lifecycle.state.label}
                      </span>
                    </div>

                    <p className={styles.infoSummary}>{t('autoDeleteSummary', language)}</p>

                    <div className={styles.infoRows}>
                      <div className={styles.infoRow}>
                        <span>{t('lastActivity', language)}</span>
                        <strong>{lifecycle.lastActivityLabel}</strong>
                      </div>
                      <div className={styles.infoRow}>
                        <span>{t('timeRemaining', language)}</span>
                        <strong>{lifecycle.timeLeftLabel}</strong>
                      </div>
                      <div className={styles.infoRow}>
                        <span>{t('nextCleanupCheckpoint', language)}</span>
                        <strong>{lifecycle.expiresAtLabel}</strong>
                      </div>
                    </div>

                    <p className={styles.infoHint}>{lifecycle.state.helper}</p>

                    <div className={styles.lockedRetention}>
                      <div className={styles.lockedRetentionCopy}>
                        <span>{t('retentionPreset', language)}</span>
                        <p>{t('longLivedBoardsUnlockSoon', language)}</p>
                      </div>

                      <div className={styles.retentionOptions}>
                        {retentionOptions.map((option) => {
                          const isActive = option.value === (board?.expires_after_days ?? 3);

                          return (
                            <button
                              key={option.value}
                              type="button"
                              className={`${styles.retentionOption} ${isActive ? styles.retentionOptionActive : ''}`}
                              disabled={!isActive}
                            >
                              <span>{option.label}</span>
                              <span className={styles.retentionOptionMeta}>
                                {isActive ? t('currentPreset', language) : t('availableAfterLogin', language)}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>

        <button
          type="button"
          className={styles.mobileMenuButton}
          aria-label={t('openBoardMenu', language)}
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((current) => !current)}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

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
                  <span className={styles.onlineValue}>{realtimeLabel}</span>
                </div>
                <OnlineAvatarStack users={displayedUsers} extraCount={extraUsers} language={language} />
              </button>

              {onlineOpen ? (
                <div className={styles.onlineDropdown}>
                  <div className={styles.onlineDropdownHeader}>
                    <strong>{realtimeLabel}</strong>
                  </div>
                  <div className={styles.onlineList}>
                    {onlineUsers.length === 0 ? (
                      <div className={styles.onlineEmpty}>
                        {t('willShowCollaboratorsWhenRealtimeConnects', language)}
                      </div>
                    ) : null}
                    {onlineUsers.map((user) => (
                      <div key={user.guest_id} className={styles.onlineRow}>
                        <div
                          className={styles.onlineAvatarLarge}
                          style={getAvatarSurfaceStyle(user.avatar_url, user.color)}
                        >
                          {!user.avatar_url && getInitial(user.display_name)}
                        </div>
                        <div>
                          <div className={styles.onlineName}>{user.display_name}</div>
                          <div className={styles.onlineMeta}>
                            {user.guest_id === identity?.id ? t('you', language) : t('guestCollaborator', language)}
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
            <span className="sr-only">{t('activity', language)}</span>
          </Button>

          <Button variant="ghost" size="sm" onClick={() => setShareOpen(true)} className={styles.iconBtn}>
            <ToolbarIcon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 13a5 5 0 0 0 7.07 0l3.54-3.54a5 5 0 0 0-7.07-7.07L12.5 4.43" />
                <path d="M14 11a5 5 0 0 0-7.07 0L3.4 14.54a5 5 0 0 0 7.07 7.07L11.5 19.57" />
              </svg>
            </ToolbarIcon>
            <span className="sr-only">{t('share', language)}</span>
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
              <span className="sr-only">{t('notifications', language)}</span>
            </Button>
          </div>

          {canManageBoard ? (
            <Button variant="secondary" size="sm" onClick={onOpenAdmin} className={styles.adminButton}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82L4.21 7.2a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
              <span>{t('admin', language)}</span>
            </Button>
          ) : null}

          <button
            type="button"
            className={styles.profileBtn}
            onClick={() => setProfileOpen(true)}
            style={getAvatarSurfaceStyle(identity?.avatarUrl, identity?.color)}
            aria-label={t('openProfile', language)}
          >
            {!identity?.avatarUrl && getInitial(identity?.displayName)}
          </button>
        </div>
      </header>

      {mobileMenuOpen ? (
        <div className={styles.mobileMenuPanel}>
          <div className={styles.mobileMenuHeader}>
            <div>
              <p className={styles.mobileMenuEyebrow}>FlowBoard</p>
              <strong>{t('boardMenu', language)}</strong>
            </div>
            <button
              type="button"
              className={styles.mobileCloseButton}
              onClick={() => setMobileMenuOpen(false)}
              aria-label={t('close', language)}
            >
              ×
            </button>
          </div>

          {showOnlineControl ? (
            <button
              type="button"
              className={styles.mobileMenuItem}
              onClick={() => setOnlineOpen((current) => !current)}
            >
              <span>{realtimeLabel}</span>
              <OnlineAvatarStack users={displayedUsers} extraCount={extraUsers} language={language} size="sm" />
            </button>
          ) : null}

          {showOnlineControl && onlineOpen ? (
            <div className={styles.mobileOnlineList}>
              {onlineUsers.length === 0 ? (
                <div className={styles.onlineEmpty}>
                  {t('willShowCollaboratorsWhenRealtimeConnects', language)}
                </div>
              ) : null}
              {onlineUsers.map((user) => (
                <div key={user.guest_id} className={styles.onlineRow}>
                  <div
                    className={styles.onlineAvatarLarge}
                    style={getAvatarSurfaceStyle(user.avatar_url, user.color)}
                  >
                    {!user.avatar_url && getInitial(user.display_name)}
                  </div>
                  <div>
                    <div className={styles.onlineName}>{user.display_name}</div>
                    <div className={styles.onlineMeta}>
                      {user.guest_id === identity?.id ? t('you', language) : t('guestCollaborator', language)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          <button
            type="button"
            className={styles.mobileMenuItem}
            onClick={() => {
              onToggleEventFlow();
              setMobileMenuOpen(false);
            }}
          >
            <span>{t('activity', language)}</span>
            <ToolbarIcon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
              </svg>
            </ToolbarIcon>
          </button>

          <button
            type="button"
            className={styles.mobileMenuItem}
            onClick={() => {
              setShareOpen(true);
              setMobileMenuOpen(false);
            }}
          >
            <span>{t('share', language)}</span>
            <ToolbarIcon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10 13a5 5 0 0 0 7.07 0l3.54-3.54a5 5 0 0 0-7.07-7.07L12.5 4.43" />
                <path d="M14 11a5 5 0 0 0-7.07 0L3.4 14.54a5 5 0 0 0 7.07 7.07L11.5 19.57" />
              </svg>
            </ToolbarIcon>
          </button>

          <button
            type="button"
            className={styles.mobileMenuItem}
            onClick={() => {
              onToggleNotifications();
              setMobileMenuOpen(false);
            }}
          >
            <span>{t('notifications', language)}</span>
            {unreadCount > 0 ? <span className={styles.mobileMenuBadge}>{unreadCount}</span> : null}
          </button>

          {canManageBoard ? (
            <button
              type="button"
              className={styles.mobileMenuItem}
              onClick={() => {
                onOpenAdmin();
                setMobileMenuOpen(false);
              }}
            >
              <span>{t('admin', language)}</span>
              <ToolbarIcon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82L4.21 7.2a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
              </ToolbarIcon>
            </button>
          ) : null}

          <button
            type="button"
            className={`${styles.mobileMenuItem} ${styles.mobileProfileItem}`}
            onClick={() => {
              setProfileOpen(true);
              setMobileMenuOpen(false);
            }}
          >
            <span>{identity?.displayName || t('profile', language)}</span>
            <span
              className={styles.mobileProfileAvatar}
              style={getAvatarSurfaceStyle(identity?.avatarUrl, identity?.color)}
              aria-hidden="true"
            >
              {!identity?.avatarUrl && getInitial(identity?.displayName)}
            </span>
          </button>
        </div>
      ) : null}

      <div className={styles.toolbarDock}>
        <section className={styles.toolbar} aria-label={t('taskSearchAndFilters', language)}>
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

          <div className={styles.filterWrap} ref={filtersRef}>
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
          </div>

          <Button size="sm" onClick={onCreateTask} className={styles.createTaskButton}>
            {t('createTask', language)}
          </Button>
        </section>
      </div>

      <main className={`${styles.main} ${mainClassName}`.trim()}>{children}</main>

      {notificationsOpen ? (
        <NotificationsMenu
          notifications={notifications}
          pending={pending}
          onMarkRead={onMarkNotificationRead}
          onMarkAllRead={onMarkAllNotificationsRead}
          onClose={onCloseNotifications}
          className={styles.notificationsOverlay}
        />
      ) : null}

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

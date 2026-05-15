import s from './Topbar.module.css';

export default function Topbar({ title, wsConnected, onAdd, addLabel, unreadCount }) {
  return (
    <header className={s.topbar}>
      <h1 className={s.title}>{title}</h1>

      <div className={s.actions}>
        {typeof unreadCount === 'number' && unreadCount > 0 && (
          <span className={s.badge} aria-label={`${unreadCount} unread`}>{unreadCount}</span>
        )}

        <span
          className={`${s.wsIndicator}${wsConnected ? '' : ' ' + s.disconnected}`}
          title={wsConnected ? 'Real-time connected' : 'Disconnected'}
          aria-label={wsConnected ? 'Real-time connected' : 'Real-time disconnected'}
        />
        <span className={s.wsLabel}>{wsConnected ? 'Live' : 'Offline'}</span>

        {onAdd && (
          <button id="btn-add-primary" className={s.btnPrimary} onClick={onAdd}>
            + {addLabel ?? 'Add'}
          </button>
        )}
      </div>
    </header>
  );
}

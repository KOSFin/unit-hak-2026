import Badge from '../Ui/Badge';
import Button from '../Ui/Button';
import styles from './Layout.module.css';

export default function Layout({
  connectionStatus,
  mode,
  onModeChange,
  onCreateTask,
  boardName,
  children,
  sidePanel,
}) {
  const isLive = connectionStatus === 'live';

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
          <Badge tone={isLive ? 'success' : 'warning'}>
            {isLive ? 'Real-time connected' : 'Real-time reconnecting'}
          </Badge>
          <div className={styles.toggle}>
            <button
              className={`${styles.toggleButton} ${mode === 'user' ? styles.toggleActive : ''}`}
              onClick={() => onModeChange('user')}
              type="button"
            >
              User
            </button>
            <button
              className={`${styles.toggleButton} ${mode === 'admin' ? styles.toggleActive : ''}`}
              onClick={() => onModeChange('admin')}
              type="button"
            >
              Admin
            </button>
          </div>
          <Button onClick={onCreateTask}>Create Task</Button>
        </div>
      </header>

      <div className={styles.body}>
        <main className={styles.main}>{children}</main>
        <aside className={styles.side}>{sidePanel}</aside>
      </div>
    </div>
  );
}

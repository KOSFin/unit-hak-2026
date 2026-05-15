import s from './Sidebar.module.css';

const items = [
  { icon: '⬛', label: 'Board', view: 'board' },
  { icon: '🔔', label: 'Notifications', view: 'notifications' },
  { icon: '📥', label: 'Incoming Tasks', view: 'incoming' },
  { icon: '⚙️', label: 'Automations', view: 'automations' },
];

export default function Sidebar({ view, onNav }) {
  return (
    <aside className={s.sidebar} aria-label="Sidebar navigation">
      <div className={s.logo}>
        <div className={s.logoIcon}>FB</div>
        FlowBoard
      </div>

      <nav className={s.nav} aria-label="Main navigation">
        <div className={s.navSection}>
          <p className={s.navLabel}>Workspace</p>
          {items.map((item) => (
            <button
              key={item.view}
              className={`${s.navItem}${view === item.view ? ' ' + s.active : ''}`}
              onClick={() => onNav(item.view)}
              aria-current={view === item.view ? 'page' : undefined}
            >
              <span className={s.navItemIcon}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <div className={s.footer}>FlowBoard v0.1.0</div>
    </aside>
  );
}

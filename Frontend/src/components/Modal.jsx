import { useEffect } from 'react';
import s from './Modal.module.css';

export default function Modal({ title, onClose, children, footer }) {
  // Close on Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div className={s.overlay} onClick={(e) => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-label={title}>
      <div className={s.panel}>
        <div className={s.header}>
          <h2 className={s.title}>{title}</h2>
          <button className={s.close} onClick={onClose} aria-label="Close modal">×</button>
        </div>
        <div className={s.body}>{children}</div>
        {footer && <div className={s.footer}>{footer}</div>}
      </div>
    </div>
  );
}

// Re-export shared CSS classes for use in consumers
export { s as modalCss };

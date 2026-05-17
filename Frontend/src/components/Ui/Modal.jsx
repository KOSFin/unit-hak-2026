import { useEffect } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Button from './Button';
import styles from './Modal.module.css';

export default function Modal({ title, onClose, children, footer }) {
  const { language } = useLocale();

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div className={styles.backdrop} onClick={onClose} role="presentation">
      <div
        className={styles.modal}
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className={styles.header}>
          <h2>{title}</h2>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label={t('close', language)} className={styles.closeButton}>
            <span aria-hidden="true">×</span>
          </Button>
        </div>
        <div className={styles.content}>{children}</div>
        {footer ? <div className={styles.footer}>{footer}</div> : null}
      </div>
    </div>
  );
}

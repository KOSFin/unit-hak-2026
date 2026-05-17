import styles from './Toast.module.css';

export default function Toast({ toast }) {
  if (!toast) {
    return null;
  }

  return (
    <div className={`${styles.toast} ${styles[toast.tone ?? 'neutral']}`} role="status" aria-live="polite">
      {toast.title ? <strong className={styles.title}>{toast.title}</strong> : null}
      <div>{toast.message}</div>
    </div>
  );
}

import styles from './Toast.module.css';

export default function Toast({ toast }) {
  if (!toast) {
    return null;
  }

  return <div className={`${styles.toast} ${styles[toast.tone ?? 'neutral']}`}>{toast.message}</div>;
}

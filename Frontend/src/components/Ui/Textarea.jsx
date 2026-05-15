import styles from './Textarea.module.css';

export default function Textarea({ label, error, className = '', ...props }) {
  return (
    <label className={`${styles.field} ${className}`}>
      {label ? <span className={styles.label}>{label}</span> : null}
      <textarea {...props} className={`${styles.textarea} ${error ? styles.invalid : ''}`} />
      {error ? <span className={styles.error}>{error}</span> : null}
    </label>
  );
}

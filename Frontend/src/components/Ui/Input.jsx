import styles from './Input.module.css';

export default function Input({ label, error, className = '', ...props }) {
  return (
    <label className={`${styles.field} ${className}`}>
      {label ? <span className={styles.label}>{label}</span> : null}
      <input {...props} className={`${styles.input} ${error ? styles.invalid : ''}`} />
      {error ? <span className={styles.error}>{error}</span> : null}
    </label>
  );
}

import styles from './Select.module.css';

export default function Select({ label, error, children, className = '', ...props }) {
  return (
    <label className={`${styles.field} ${className}`}>
      {label ? <span className={styles.label}>{label}</span> : null}
      <select {...props} className={`${styles.select} ${error ? styles.invalid : ''}`}>
        {children}
      </select>
      {error ? <span className={styles.error}>{error}</span> : null}
    </label>
  );
}

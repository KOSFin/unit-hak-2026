import styles from './Button.module.css';

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  block = false,
  type = 'button',
  ...props
}) {
  const className = [
    styles.button,
    styles[variant],
    styles[size],
    block ? styles.block : '',
    props.className ?? '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button {...props} type={type} className={className}>
      {children}
    </button>
  );
}

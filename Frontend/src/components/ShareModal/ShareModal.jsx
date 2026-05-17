import Modal from '../Ui/Modal';
import Button from '../Ui/Button';
import styles from './ShareModal.module.css';

export default function ShareModal({ board, onClose }) {
  const url = window.location.origin + board.board_url;

  const handleCopy = () => {
    navigator.clipboard.writeText(url);
    alert('Copied to clipboard');
  };

  return (
    <Modal title="Share Board" onClose={onClose} footer={
      <div className={styles.footer}>
        <Button onClick={onClose} variant="ghost">Close</Button>
      </div>
    }>
      <div className={styles.content}>
        <p className={styles.text}>Anyone with this link can access this MVP board.</p>
        <div className={styles.inputGroup}>
          <input readOnly value={url} className={styles.input} />
          <Button onClick={handleCopy}>Copy link</Button>
        </div>
      </div>
    </Modal>
  );
}

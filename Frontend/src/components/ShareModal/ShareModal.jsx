import { useState } from 'react';

import { getBoardPublicUrl, resolveAppUrl } from '../../api/client';
import Modal from '../Ui/Modal';
import Button from '../Ui/Button';
import styles from './ShareModal.module.css';

export default function ShareModal({ board, onClose }) {
  const url = resolveAppUrl(board.board_url || getBoardPublicUrl(board.public_id));
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
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
          <Button onClick={handleCopy}>{copied ? 'Copied' : 'Copy link'}</Button>
        </div>
      </div>
    </Modal>
  );
}

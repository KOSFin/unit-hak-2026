import { useState } from 'react';

import { getBoardPublicUrl, resolveAppUrl } from '../../api/client';
import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Modal from '../Ui/Modal';
import Button from '../Ui/Button';
import styles from './ShareModal.module.css';

export default function ShareModal({ board, onClose }) {
  const { language } = useLocale();
  const url = resolveAppUrl(board.board_url || getBoardPublicUrl(board.public_id));
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <Modal title={t('shareBoard', language)} onClose={onClose} size="sm">
      <div className={styles.content}>
        <p className={styles.text}>{t('anyoneWithLinkCanAccess', language)}</p>
        <div className={styles.linkRow}>
          <input readOnly value={url} className={styles.input} />
          <Button onClick={handleCopy} className={styles.copyButton}>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M10 13a5 5 0 0 0 7.07 0l3.54-3.54a5 5 0 0 0-7.07-7.07L12.5 4.43" />
              <path d="M14 11a5 5 0 0 0-7.07 0L3.4 14.54a5 5 0 0 0 7.07 7.07L11.5 19.57" />
            </svg>
            <span>{copied ? t('copied', language) : t('copyBoardLinkCta', language)}</span>
          </Button>
        </div>
        <p className={styles.helper}>{copied ? t('copied', language) : t('copyLink', language)}</p>
      </div>
    </Modal>
  );
}

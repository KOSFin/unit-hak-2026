import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { createBoard } from '../../api/boardsApi';
import { getBoardPublicUrl, resolveAppUrl } from '../../api/client';
import { uploadImage } from '../../api/uploadsApi';
import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import { getGuestIdentity } from '../../utils/guest';
import Button from '../Ui/Button';
import Input from '../Ui/Input';
import Select from '../Ui/Select';
import styles from './LandingPage.module.css';

export default function LandingPage() {
  const navigate = useNavigate();
  const { language } = useLocale();
  const identity = getGuestIdentity();
  const [name, setName] = useState('');
  const [retention, setRetention] = useState('3');
  const [adminAccess, setAdminAccess] = useState('creator-only');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [createdBoard, setCreatedBoard] = useState(null);
  const [copied, setCopied] = useState(false);
  const [startOpen, setStartOpen] = useState(false);
  const fileInputRef = useRef(null);

  const RETENTION_OPTIONS = [
    { value: '3', label: language === 'ru' ? '3 дня' : '3 days' },
    { value: '7', label: language === 'ru' ? '7 дней' : '7 days' },
    { value: '30', label: language === 'ru' ? '30 дней' : '30 days' },
    { value: '365', label: language === 'ru' ? '1 год' : '1 year' },
    { value: 'forever', label: language === 'ru' ? 'Не удалять' : 'Do not delete' },
  ];

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError(t('invalidInput', language));
        return;
      }
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result);
      reader.readAsDataURL(file);
      setError(null);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError(t('boardName', language) + ' ' + t('invalidInput', language));
      return;
    }
    
    setPending(true);
    setError(null);

    try {
      let imagePath = null;
      if (imageFile) {
        const uploadRes = await uploadImage(imageFile);
        imagePath = uploadRes.path;
      }

      const board = await createBoard({
        name: name.trim(),
        retention_days: parseInt(retention, 10),
        image_path: imagePath,
        creator_guest_id: identity.id,
        allow_guest_admin: adminAccess === 'all-guests',
      });

      setCreatedBoard(board);
    } catch (err) {
      setError(err.response?.data?.detail || t('error', language));
    } finally {
      setPending(false);
    }
  };

  const boardUrl = createdBoard
    ? resolveAppUrl(createdBoard.board_url || getBoardPublicUrl(createdBoard.public_id))
    : '';

  const copyLink = async () => {
    await navigator.clipboard.writeText(boardUrl);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  const openStartModal = () => {
    setStartOpen(true);
  };

  const closeStartModal = () => {
    if (!pending) {
      setStartOpen(false);
    }
  };

  const creationForm = createdBoard ? (
    <div className={styles.createdCard}>
      <p className={styles.formKicker}>{t('boardCreated', language)}</p>
      <h2>{t('yourMvpBoardIsReady', language)}</h2>
      <div className={styles.linkBox}>
        <input readOnly value={boardUrl} className={styles.linkInput} />
        <Button onClick={copyLink}>{copied ? t('copied', language) : t('copyLink', language)}</Button>
      </div>
      <Button
        className={styles.openBtn}
        onClick={() => navigate(`/board/${createdBoard.public_id}`)}
      >
        {t('openBoard', language)}
      </Button>
    </div>
  ) : (
    <form className={styles.formCard} onSubmit={handleCreate}>
      <p className={styles.formKicker}>{t('boardSetup', language)}</p>
      <h2>{t('createBoardTitle', language)}</h2>
      <p className={styles.formLead}>{t('landingModalFormLead', language)}</p>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.formGroup}>
        <Input
          label={t('boardName', language)}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={t('egHackathonProject', language)}
        />
      </div>

      <div className={styles.formGroup}>
        <label className={styles.label}>{t('boardImageOptional', language)}</label>
        <div className={styles.imageUpload} onClick={() => fileInputRef.current?.click()}>
          {imagePreview ? (
            <img src={imagePreview} alt="Preview" className={styles.preview} />
          ) : (
            <div className={styles.uploadPlaceholder}>{t('clickToUploadLogo', language)}</div>
          )}
        </div>
        <input
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          ref={fileInputRef}
          onChange={handleImageChange}
        />
      </div>

      <div className={styles.formGroup}>
        <Select
          label={t('retentionInactivityExpiration', language)}
          value={retention}
          onChange={(e) => setRetention(e.target.value)}
        >
          {RETENTION_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </Select>
        {retention !== '3' && (
          <div className={styles.comingSoon}>
            <p>{t('longTermBoardsRequireAccount', language)}</p>
            <Button variant="secondary" size="sm" disabled>
              {t('signInSoon', language)}
            </Button>
          </div>
        )}
      </div>

      <div className={styles.formGroup}>
        <div className={styles.optionLabel}>{t('adminAccess', language)}</div>
        <div className={styles.accessGrid}>
          <label className={`${styles.accessCard} ${adminAccess === 'creator-only' ? styles.accessCardActive : ''}`}>
            <input
              type="radio"
              name="admin-access"
              value="creator-only"
              checked={adminAccess === 'creator-only'}
              onChange={(event) => setAdminAccess(event.target.value)}
            />
            <strong>{t('creatorOnlyAdmin', language)}</strong>
            <span>{t('creatorOnlyAdminHint', language)}</span>
          </label>

          <label className={`${styles.accessCard} ${adminAccess === 'all-guests' ? styles.accessCardActive : ''}`}>
            <input
              type="radio"
              name="admin-access"
              value="all-guests"
              checked={adminAccess === 'all-guests'}
              onChange={(event) => setAdminAccess(event.target.value)}
            />
            <strong>{t('allGuestsAdmin', language)}</strong>
            <span>{t('allGuestsAdminHint', language)}</span>
          </label>
        </div>
      </div>

      <Button type="submit" disabled={pending || retention !== '3'} className={styles.submitBtn}>
        {pending ? t('loading', language) : retention === '3' ? t('create', language) + ' ' + t('flowboard', language) : `3 ${t('daysLeft', language)} MVP only`}
      </Button>
    </form>
  );

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <header className={styles.header}>
          <div className={styles.brand}>
            <span className={styles.logo} aria-hidden="true">
              <span></span>
            </span>
            <span>{t('flowboard', language)}</span>
          </div>
          <nav className={styles.nav} aria-label="Landing navigation">
            <a
              className={styles.githubLink}
              href="https://github.com/KOSFin/unit-hak-2026"
              target="_blank"
              rel="noreferrer"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.52 2.87 8.35 6.84 9.7.5.1.68-.22.68-.49 0-.24-.01-.88-.01-1.73-2.78.62-3.37-1.37-3.37-1.37-.45-1.19-1.11-1.51-1.11-1.51-.91-.64.07-.63.07-.63 1 .07 1.53 1.06 1.53 1.06.9 1.57 2.36 1.12 2.94.86.09-.67.35-1.12.63-1.38-2.22-.26-4.56-1.14-4.56-5.07 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.71 0 0 .84-.28 2.75 1.05A9.36 9.36 0 0 1 12 6.95c.85 0 1.7.12 2.5.34 1.91-1.33 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.72 1.03 1.63 1.03 2.75 0 3.94-2.34 4.8-4.57 5.06.36.32.68.94.68 1.9 0 1.38-.01 2.49-.01 2.83 0 .27.18.59.69.49A10.12 10.12 0 0 0 22 12.26C22 6.58 17.52 2 12 2Z" />
              </svg>
              <span>KOSFin/unit-hak-2026</span>
            </a>
            <Button size="sm" onClick={openStartModal}>{t('start', language)}</Button>
          </nav>
        </header>

        <main className={styles.heroContent}>
          <p className={styles.eyebrow}>{t('landingEyebrow', language)}</p>
          <h1 className={styles.heroTitle} data-title={t('flowboard', language)}>{t('flowboard', language)}</h1>
          <p className={styles.heroDescription}>{t('landingDescription', language)}</p>
          <div className={styles.heroActions}>
            <Button onClick={openStartModal}>{t('start', language)}</Button>
          </div>
        </main>
      </section>

      <footer className={styles.footer}>
        <p>(с) Pencil team.</p>
        <p>{t('createdForUnitHack', language)}</p>
      </footer>

      {startOpen ? (
        <div className={styles.startOverlay} role="dialog" aria-modal="true" aria-label={t('createTemporaryBoard', language)}>
          <button
            type="button"
            className={styles.startBackdrop}
            onClick={closeStartModal}
            aria-label={t('close', language)}
          />
          <div className={styles.startModal}>
            <button
              type="button"
              className={styles.closeButton}
              onClick={closeStartModal}
              aria-label={t('close', language)}
            >
              ×
            </button>
            <aside className={styles.boardsPane}>
              <p className={styles.formKicker}>{t('createdBoards', language)}</p>
              {createdBoard ? (
                <button
                  type="button"
                  className={styles.createdPreview}
                  onClick={() => navigate(`/board/${createdBoard.public_id}`)}
                >
                  <strong>{createdBoard.name}</strong>
                  <span>{t('openBoard', language)}</span>
                </button>
              ) : (
                <div className={styles.emptyBoards}>
                  <strong>{t('landingNoBoardsYet', language)}</strong>
                  <span>{t('landingNoBoardsHint', language)}</span>
                </div>
              )}
              <div className={styles.kanbanMock} aria-hidden="true">
                <div>
                  <span></span>
                  <strong>{t('landingMockTodo', language)}</strong>
                  <p>{t('landingMockApi', language)}</p>
                </div>
                <div>
                  <span></span>
                  <strong>{t('landingMockDoing', language)}</strong>
                  <p>{t('landingMockRealtime', language)}</p>
                </div>
                <div>
                  <span></span>
                  <strong>{t('landingMockDone', language)}</strong>
                  <p>{t('landingMockShip', language)}</p>
                </div>
              </div>
            </aside>
            <section className={styles.formPane}>{creationForm}</section>
          </div>
        </div>
      ) : null}
    </div>
  );
}

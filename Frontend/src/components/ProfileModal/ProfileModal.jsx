import { useRef, useState } from 'react';

import { updateGuestProfile as updateGuestProfileRequest } from '../../api/guestApi';
import { uploadImage } from '../../api/uploadsApi';
import { useLocale } from '../../contexts/LocaleContext';
import { getAvatarSurfaceStyle } from '../../utils/imagePlaceholders';
import { t } from '../../utils/i18n';
import Modal from '../Ui/Modal';
import Input from '../Ui/Input';
import Button from '../Ui/Button';
import { updateGuestIdentity } from '../../utils/guest';
import styles from './ProfileModal.module.css';

export default function ProfileModal({ identity, onClose, onUpdate }) {
  const { language, setLanguage } = useLocale();
  const [displayName, setDisplayName] = useState(identity.displayName || '');
  const [avatarUrl, setAvatarUrl] = useState(identity.avatarUrl);
  const [pending, setPending] = useState(false);
  const fileInputRef = useRef(null);

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setPending(true);
    try {
      const res = await uploadImage(file);
      setAvatarUrl(res.url);
    } catch {
      alert(t('failedToUploadAvatar', language));
    } finally {
      setPending(false);
    }
  };

  const handleSubmit = async () => {
    if (!displayName.trim()) return;
    setPending(true);
    try {
      const profile = await updateGuestProfileRequest(identity.id, {
        guest_id: identity.id,
        display_name: displayName.trim(),
        color: identity.color,
        avatar_url: avatarUrl,
      });
      const updated = updateGuestIdentity({
        displayName: profile.display_name,
        avatarUrl: profile.avatar_url,
        color: profile.color ?? identity.color,
      });
      onUpdate(updated);
    } catch {
      alert(t('failedToSaveProfile', language));
    } finally {
      setPending(false);
    }
  };

  return (
    <Modal
      title={t('guestProfile', language)}
      onClose={onClose}
      footer={
        <div className={styles.footer}>
          <Button variant="ghost" onClick={onClose}>{t('cancel', language)}</Button>
          <Button onClick={handleSubmit} disabled={pending || !displayName.trim()}>
            {t('save', language)}
          </Button>
        </div>
      }
    >
      <div className={styles.content}>
        <div className={styles.avatarSection}>
          <div
            className={styles.avatarPreview}
            style={getAvatarSurfaceStyle(avatarUrl, identity.color)}
            onClick={() => fileInputRef.current?.click()}
          >
            {!avatarUrl ? (
              <span className={styles.avatarInitial}>{displayName.charAt(0).toUpperCase()}</span>
            ) : null}
            <div className={styles.avatarOverlay}>{t('changeAvatar', language)}</div>
          </div>
          <input 
            type="file" 
            accept="image/*" 
            style={{ display: 'none' }} 
            ref={fileInputRef}
            onChange={handleAvatarChange}
          />
        </div>

        <Input 
          label={t('displayName', language)}
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder={`${t('guest', language)} 123`}
        />

        <div className={styles.languageSection}>
          <label className={styles.languageLabel}>
            <span>{t('selectLanguage', language)}</span>
          </label>
          <div className={styles.languageOptions}>
            <button
              type="button"
              className={`${styles.languageBtn} ${language === 'ru' ? styles.languageBtnActive : ''}`}
              onClick={() => setLanguage('ru')}
              title={t('russian', language)}
            >
              <span className={styles.flag}>🇷🇺</span>
              <span>{t('russian', language)}</span>
            </button>
            <button
              type="button"
              className={`${styles.languageBtn} ${language === 'en' ? styles.languageBtnActive : ''}`}
              onClick={() => setLanguage('en')}
              title={t('english', language)}
            >
              <span className={styles.flag}>🇬🇧</span>
              <span>{t('english', language)}</span>
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}

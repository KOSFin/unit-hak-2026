import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { createBoard } from '../../api/boardsApi';
import { getBoardPublicUrl, resolveAppUrl } from '../../api/client';
import { uploadImage } from '../../api/uploadsApi';
import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Button from '../Ui/Button';
import Input from '../Ui/Input';
import Select from '../Ui/Select';
import styles from './LandingPage.module.css';

export default function LandingPage() {
  const navigate = useNavigate();
  const { language } = useLocale();
  const [name, setName] = useState('');
  const [retention, setRetention] = useState('3');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [createdBoard, setCreatedBoard] = useState(null);
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef(null);

  const RETENTION_OPTIONS = [
    { value: '3', label: language === 'ru' ? '3 дня (MVP временная доска)' : '3 days (MVP temporary board)' },
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

  if (createdBoard) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <h1 className={styles.title}>{t('boardCreated', language)}</h1>
          <p className={styles.subtitle}>{t('yourMvpBoardIsReady', language)}</p>
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
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <form className={styles.card} onSubmit={handleCreate}>
        <h1 className={styles.title}>{t('flowboard', language)}</h1>
        <p className={styles.subtitle}>{t('createTemporaryBoard', language)}</p>

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

        <Button type="submit" disabled={pending || retention !== '3'} className={styles.submitBtn}>
          {pending ? t('loading', language) : retention === '3' ? t('create', language) + ' ' + t('flowboard', language) : `3 ${t('daysLeft', language)} MVP only`}
        </Button>
      </form>
    </div>
  );
}

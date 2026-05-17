import { useState, useRef } from 'react';
import Modal from '../Ui/Modal';
import Input from '../Ui/Input';
import Button from '../Ui/Button';
import { apiClient } from '../../api/client';
import { updateGuestIdentity } from '../../utils/guest';
import styles from './ProfileModal.module.css';

export default function ProfileModal({ identity, onClose, onUpdate }) {
  const [displayName, setDisplayName] = useState(identity.displayName || '');
  const [avatarUrl, setAvatarUrl] = useState(identity.avatarUrl);
  const [pending, setPending] = useState(false);
  const fileInputRef = useRef(null);

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setPending(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiClient.post('/api/uploads', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAvatarUrl(res.data.url);
    } catch (err) {
      alert("Failed to upload avatar");
    } finally {
      setPending(false);
    }
  };

  const handleSubmit = () => {
    if (!displayName.trim()) return;
    const updated = updateGuestIdentity({
      displayName: displayName.trim(),
      avatarUrl,
    });
    onUpdate(updated);
  };

  return (
    <Modal
      title="Guest Profile"
      onClose={onClose}
      footer={
        <div className={styles.footer}>
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={pending || !displayName.trim()}>
            Save Profile
          </Button>
        </div>
      }
    >
      <div className={styles.content}>
        <div className={styles.avatarSection}>
          <div 
            className={styles.avatarPreview} 
            style={{ backgroundColor: avatarUrl ? 'transparent' : identity.color }}
            onClick={() => fileInputRef.current?.click()}
          >
            {avatarUrl ? (
              <img src={avatarUrl} alt="Avatar" className={styles.avatarImg} />
            ) : (
              <span className={styles.avatarInitial}>{displayName.charAt(0).toUpperCase()}</span>
            )}
            <div className={styles.avatarOverlay}>Change</div>
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
          label="Display Name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Guest 123"
        />
      </div>
    </Modal>
  );
}

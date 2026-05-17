import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { createBoard } from '../../api/boardsApi';
import { apiClient } from '../../api/client';
import Button from '../Ui/Button';
import Input from '../Ui/Input';
import Select from '../Ui/Select';
import styles from './LandingPage.module.css';

export default function LandingPage() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [retention, setRetention] = useState('3');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const [createdBoard, setCreatedBoard] = useState(null);
  const fileInputRef = useRef(null);

  const RETENTION_OPTIONS = [
    { value: '3', label: '3 days (No account required)' },
    { value: '7', label: '7 days', disabled: true },
    { value: '30', label: '30 days', disabled: true },
    { value: '365', label: '1 year', disabled: true },
    { value: 'forever', label: 'Forever', disabled: true },
  ];

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file');
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
      setError('Board name is required');
      return;
    }
    
    setPending(true);
    setError(null);

    try {
      let imagePath = null;
      if (imageFile) {
        const formData = new FormData();
        formData.append('file', imageFile);
        const uploadRes = await apiClient.post('/api/uploads', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        imagePath = uploadRes.data.url;
      }

      const board = await createBoard({
        name: name.trim(),
        retention_days: parseInt(retention, 10),
        image_path: imagePath,
      });

      setCreatedBoard(board);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create board');
    } finally {
      setPending(false);
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.origin + createdBoard.board_url);
    // basic visual feedback
    alert("Copied!");
  };

  if (createdBoard) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <h1 className={styles.title}>Board Created</h1>
          <p className={styles.subtitle}>Your MVP board is ready.</p>
          <div className={styles.linkBox}>
            <input 
              readOnly 
              value={window.location.origin + createdBoard.board_url} 
              className={styles.linkInput} 
            />
            <Button onClick={copyLink}>Copy link</Button>
          </div>
          <Button variant="primary" className={styles.openBtn} onClick={() => navigate(`/board/${createdBoard.public_id}`)}>
            Open Board
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <form className={styles.card} onSubmit={handleCreate}>
        <h1 className={styles.title}>FlowBoard</h1>
        <p className={styles.subtitle}>Create a temporary event-driven kanban board.</p>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.formGroup}>
          <Input 
            label="Board Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="E.g., Hackathon Project"
          />
        </div>

        <div className={styles.formGroup}>
           <label className={styles.label}>Board Image (Optional)</label>
           <div className={styles.imageUpload} onClick={() => fileInputRef.current?.click()}>
              {imagePreview ? (
                <img src={imagePreview} alt="Preview" className={styles.preview} />
              ) : (
                <div className={styles.uploadPlaceholder}>Click to upload logo</div>
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
            label="Retention (Inactivity Expiration)" 
            value={retention} 
            onChange={(e) => setRetention(e.target.value)}
          >
            {RETENTION_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </Select>
          {retention !== '3' && (
             <div className={styles.comingSoon}>Long-term boards require an account. Authentication is coming soon.</div>
          )}
        </div>

        <Button type="submit" disabled={pending} className={styles.submitBtn}>
          {pending ? 'Creating...' : 'Create Board'}
        </Button>
      </form>
    </div>
  );
}

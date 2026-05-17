import { useState, useEffect } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Button from '../Ui/Button';
import Badge from '../Ui/Badge';
import Input from '../Ui/Input';
import Modal from '../Ui/Modal';
import Select from '../Ui/Select';
import Textarea from '../Ui/Textarea';
import styles from './TaskModal.module.css';

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

function splitTags(value) {
  return value
    .split(/[\s,]+/g)
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function taskToForm(columns, task) {
  return {
    title: task?.title ?? '',
    description: task?.description ?? '',
    priority: task?.priority ?? 'MEDIUM',
    tags: task?.tags ?? [],
    deadline: task?.deadline ? task.deadline.slice(0, 16) : '',
    columnId: task?.column_id ?? columns[0]?.id ?? '',
  };
}

export default function TaskModal({
  boardId,
  columns,
  task,
  pending,
  onClose,
  onSubmit,
  onDelete,
}) {
  const { language } = useLocale();
  const [form, setForm] = useState(taskToForm(columns, task));
  const [errors, setErrors] = useState({});
  const [tagInput, setTagInput] = useState('');

  useEffect(() => {
    if (task && task.id) {
      window.dispatchEvent(new CustomEvent('task-edit-start', { detail: task.id }));
    }
    return () => {
      if (task && task.id) {
        window.dispatchEvent(new CustomEvent('task-edit-end', { detail: task.id }));
      }
    };
  }, [task]);

  const handleChange = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const addTags = (tagsToAdd) => {
    if (!tagsToAdd.length) {
      return;
    }
    setForm((current) => {
      const existing = new Set(current.tags);
      const merged = [...current.tags];
      tagsToAdd.forEach((tag) => {
        if (!existing.has(tag)) {
          existing.add(tag);
          merged.push(tag);
        }
      });
      return { ...current, tags: merged };
    });
  };

  const commitTagInput = () => {
    const tagsToAdd = splitTags(tagInput);
    if (tagsToAdd.length) {
      addTags(tagsToAdd);
      setTagInput('');
    }
  };

  const handleTagKeyDown = (event) => {
    const shouldCommit = ['Enter', 'Tab', ',', ' '].includes(event.key);
    if (shouldCommit) {
      if (tagInput.trim()) {
        event.preventDefault();
        commitTagInput();
      }
      return;
    }

    if (event.key === 'Backspace' && !tagInput && form.tags.length > 0) {
      setForm((current) => ({ ...current, tags: current.tags.slice(0, -1) }));
    }
  };

  const handleTagBlur = () => {
    commitTagInput();
  };

  const handleRemoveTag = (tagToRemove) => {
    setForm((current) => ({
      ...current,
      tags: current.tags.filter((tag) => tag !== tagToRemove),
    }));
  };

  const handleSubmit = async () => {
    if (!form.title.trim()) {
      setErrors({ title: t('titleIsRequired', language) });
      return;
    }

    const payload = {
      board_id: boardId,
      column_id: form.columnId,
      title: form.title.trim(),
      description: form.description.trim() || null,
      priority: form.priority,
      tags: form.tags,
      deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
    };

    await onSubmit(payload);
  };

  return (
    <Modal
      title={task ? t('editTask', language) : t('createTaskTitle', language)}
      onClose={onClose}
      footer={
        <div className={styles.footer}>
          {task ? (
            <Button variant="danger" onClick={() => onDelete(task)} disabled={pending}>
              {t('delete', language)}
            </Button>
          ) : null}
          <Button variant="ghost" onClick={onClose}>
            {t('cancel', language)}
          </Button>
          <Button onClick={handleSubmit} disabled={pending}>
            {pending ? t('saving', language) : task ? t('saveChanges', language) : t('createTask', language)}
          </Button>
        </div>
      }
    >
      <div className={styles.grid}>
        <Input
          label={t('taskTitle', language)}
          value={form.title}
          onChange={handleChange('title')}
          error={errors.title}
          placeholder={t('addClearTaskTitle', language)}
        />
        <Select label={t('priority', language)} value={form.priority} onChange={handleChange('priority')}>
          {PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {t(priority.toLowerCase(), language)}
            </option>
          ))}
        </Select>
        <Select label={t('taskColumn', language)} value={form.columnId} onChange={handleChange('columnId')}>
          {columns.map((column) => (
            <option key={column.id} value={column.id}>
              {column.title}
            </option>
          ))}
        </Select>
        <Input
          label={t('deadline', language)}
          type="datetime-local"
          value={form.deadline}
          onChange={handleChange('deadline')}
        />
        <div className={`${styles.full} ${styles.tagField}`}>
          <span className={styles.tagLabel}>{t('tags', language)}</span>
          <div className={styles.tagControl}>
            {form.tags.map((tag) => (
              <span key={tag} className={styles.tagChip}>
                <Badge tone={tag === 'urgent' ? 'danger' : 'accent'}>{tag}</Badge>
                <button
                  type="button"
                  className={styles.tagRemove}
                  onClick={() => handleRemoveTag(tag)}
                  aria-label={`${t('removeTag', language)} ${tag}`}
                >
                  x
                </button>
              </span>
            ))}
            <input
              className={styles.tagInput}
              value={tagInput}
              onChange={(event) => setTagInput(event.target.value)}
              onKeyDown={handleTagKeyDown}
              onBlur={handleTagBlur}
              placeholder={t('tagPlaceholder', language)}
            />
          </div>
        </div>
        <Textarea
          className={styles.full}
          label={t('description', language)}
          value={form.description}
          onChange={handleChange('description')}
          placeholder={t('giveTeamContext', language)}
        />
      </div>
    </Modal>
  );
}

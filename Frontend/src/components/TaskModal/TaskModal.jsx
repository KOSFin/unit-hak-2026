import { useMemo, useState } from 'react';

import Button from '../Ui/Button';
import Badge from '../Ui/Badge';
import Input from '../Ui/Input';
import Modal from '../Ui/Modal';
import Select from '../Ui/Select';
import Textarea from '../Ui/Textarea';
import styles from './TaskModal.module.css';

const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

function normalizeTagsInput(value) {
  const endsWithSpace = /\s$/.test(value);
  const normalized = value.replace(/[\s,]+/g, ' ').trimStart();
  if (endsWithSpace && normalized) {
    return `${normalized} `;
  }
  return normalized;
}

function parseTags(value) {
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
    tags: (task?.tags ?? []).join(' '),
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
  const [form, setForm] = useState(taskToForm(columns, task));
  const [errors, setErrors] = useState({});

  const handleChange = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleTagsChange = (event) => {
    setForm((current) => ({ ...current, tags: normalizeTagsInput(event.target.value) }));
  };

  const tagPreview = useMemo(() => parseTags(form.tags), [form.tags]);

  const handleSubmit = async () => {
    if (!form.title.trim()) {
      setErrors({ title: 'Title is required' });
      return;
    }

    const payload = {
      board_id: boardId,
      column_id: form.columnId,
      title: form.title.trim(),
      description: form.description.trim() || null,
      priority: form.priority,
      tags: parseTags(form.tags),
      deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
    };

    await onSubmit(payload);
  };

  return (
    <Modal
      title={task ? 'Edit task' : 'Create task'}
      onClose={onClose}
      footer={
        <div className={styles.footer}>
          {task ? (
            <Button variant="danger" onClick={() => onDelete(task)} disabled={pending}>
              Delete
            </Button>
          ) : null}
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={pending}>
            {pending ? 'Saving…' : task ? 'Save changes' : 'Create task'}
          </Button>
        </div>
      }
    >
      <div className={styles.grid}>
        <Input
          label="Title"
          value={form.title}
          onChange={handleChange('title')}
          error={errors.title}
          placeholder="Add a clear task title"
        />
        <Select label="Priority" value={form.priority} onChange={handleChange('priority')}>
          {PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </Select>
        <Select label="Column" value={form.columnId} onChange={handleChange('columnId')}>
          {columns.map((column) => (
            <option key={column.id} value={column.id}>
              {column.title}
            </option>
          ))}
        </Select>
        <Input
          label="Deadline"
          type="datetime-local"
          value={form.deadline}
          onChange={handleChange('deadline')}
        />
        <Input
          className={styles.full}
          label="Tags"
          value={form.tags}
          onChange={handleTagsChange}
          placeholder="urgent backend auto-progress"
        />
        {tagPreview.length > 0 ? (
          <div className={`${styles.full} ${styles.tagPreview}`}>
            {tagPreview.map((tag) => (
              <Badge key={tag} tone={tag === 'urgent' ? 'danger' : 'accent'}>
                {tag}
              </Badge>
            ))}
          </div>
        ) : null}
        <Textarea
          className={styles.full}
          label="Description"
          value={form.description}
          onChange={handleChange('description')}
          placeholder="Give the team enough context to act without asking follow-up questions."
        />
      </div>
    </Modal>
  );
}

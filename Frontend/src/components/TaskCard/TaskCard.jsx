import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import { useLocale } from '../../contexts/LocaleContext';
import { t, formatDate } from '../../utils/i18n';
import Badge from '../Ui/Badge';
import styles from './TaskCard.module.css';

function getPriorityTone(priority) {
  if (priority === 'CRITICAL') return 'danger';
  if (priority === 'HIGH') return 'warning';
  return 'neutral';
}

function getPriorityLabel(priority, locale) {
  const labels = {
    CRITICAL: t('critical', locale),
    HIGH: t('high', locale),
    MEDIUM: t('medium', locale),
    LOW: t('low', locale),
  };
  return labels[priority] || priority;
}

function getInitial(name = '') {
  return name.trim().charAt(0).toUpperCase() || '?';
}

function ActivityIndicator({ user, label }) {
  if (!user) return null;

  return (
    <div className={styles.activityBadge}>
      <span
        className={styles.activityAvatar}
        style={{
          backgroundColor: user.color || 'var(--surface-muted)',
          backgroundImage: user.avatar_url ? `url(${user.avatar_url})` : 'none',
        }}
        aria-hidden="true"
      >
        {!user.avatar_url && getInitial(user.display_name)}
      </span>
      <span className={styles.activityText}>
        <span className={styles.activityLabel}>{label}</span>
        <span className={styles.activityName}>{user.display_name}</span>
      </span>
    </div>
  );
}

function TaskCardContent({ task, editingUsers, draggingUsers, locale }) {
  const formatDeadline = (value) => {
    return formatDate(value, locale);
  };
  const activityUser = editingUsers?.[0] ?? draggingUsers?.[0] ?? null;
  const activityLabel = editingUsers?.length
    ? t('editingBy', locale)
    : draggingUsers?.length
      ? t('movingBy', locale)
      : null;

  return (
    <>
      {activityUser && activityLabel ? (
        <ActivityIndicator user={activityUser} label={activityLabel} />
      ) : null}

      <div className={styles.header}>
        <span className={styles.id}>#{task.id.slice(0, 8)}</span>
        <Badge tone={getPriorityTone(task.priority)}>{getPriorityLabel(task.priority, locale)}</Badge>
      </div>

      <h3 className={styles.title}>{task.title}</h3>
      {task.description ? <p className={styles.description}>{task.description}</p> : null}

      <div className={styles.meta}>
        {(task.tags ?? []).map((tag) => (
          <Badge key={tag} tone={tag === 'urgent' ? 'danger' : 'accent'}>
            {tag}
          </Badge>
        ))}
      </div>

      <div className={styles.footer}>
        <span>{task.status}</span>
        <span>{task.deadline ? formatDeadline(task.deadline) : t('noDeadline', locale)}</span>
      </div>
    </>
  );
}

export function TaskCardPreview({ task, locale = 'ru' }) {
  return (
    <div className={`${styles.card} ${styles.overlay}`}>
      <TaskCardContent task={task} locale={locale} />
    </div>
  );
}

export default function TaskCard({ task, onOpen, editingUsers, draggingUsers, dragDisabled = false }) {
  const { language } = useLocale();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `task:${task.id}`,
    data: {
      type: 'task',
      taskId: task.id,
      columnId: task.column_id,
    },
    disabled: dragDisabled,
  });
  
  const isEditing = editingUsers?.length > 0;
  const isOtherDragging = draggingUsers?.length > 0 && !isDragging;

  return (
    <button
      ref={setNodeRef}
      type="button"
      className={`${styles.card} ${dragDisabled ? styles.cardStatic : ''} ${isDragging ? styles.dragging : ''} ${isEditing ? styles.cardEditing : ''} ${isOtherDragging ? styles.cardMoving : ''}`}
      style={{
        transform: CSS.Translate.toString(transform),
        transition,
        '--indicator-color': isEditing ? editingUsers[0].color : (isOtherDragging ? draggingUsers[0].color : 'transparent')
      }}
      onClick={() => onOpen(task)}
      {...attributes}
      {...listeners}
    >
      <TaskCardContent task={task} editingUsers={editingUsers} draggingUsers={draggingUsers} locale={language} />
    </button>
  );
}

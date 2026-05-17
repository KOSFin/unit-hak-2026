import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import { useLocale } from '../../contexts/LocaleContext';
import { t, formatDate } from '../../utils/i18n';
import { getAvatarSurfaceStyle } from '../../utils/imagePlaceholders';
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

function formatPresenceNames(users, locale) {
  const visibleNames = users
    .slice(0, 2)
    .map((user) => user.display_name || t('guest', locale));
  const extraCount = Math.max(0, users.length - 2);

  if (extraCount === 0) {
    return visibleNames.join(', ');
  }

  return [
    visibleNames.join(', '),
    t('andMoreCollaborators', locale),
    extraCount,
    t('moreCollaboratorsSuffix', locale),
  ]
    .filter(Boolean)
    .join(' ');
}

function getPresenceLabel(kind, count, locale) {
  if (kind === 'editing') {
    return count > 1 ? t('editingMany', locale) : t('editingBy', locale);
  }

  return count > 1 ? t('movingMany', locale) : t('movingBy', locale);
}

function ActivityIndicator({ users = [], label, locale }) {
  if (!users.length) return null;

  const visibleUsers = users.slice(0, 2);
  const extraCount = Math.max(0, users.length - 2);
  const namesLabel = formatPresenceNames(users, locale);

  return (
    <div className={styles.activityBadge} aria-label={`${label} ${namesLabel}`}>
      <span className={styles.activityAvatarStack} aria-hidden="true">
        {visibleUsers.map((user) => (
          <span
            key={user.guest_id}
            className={styles.activityAvatar}
            style={getAvatarSurfaceStyle(user.avatar_url, user.color)}
          >
            {!user.avatar_url && getInitial(user.display_name)}
          </span>
        ))}
        {extraCount > 0 ? <span className={`${styles.activityAvatar} ${styles.activityExtra}`}>+{extraCount}</span> : null}
      </span>
      <span className={styles.activityText}>
        <span className={styles.activityLabel}>{label}</span>
        <span className={styles.activityName}>{namesLabel}</span>
      </span>
    </div>
  );
}

function TaskCardContent({ task, editingUsers, draggingUsers, locale }) {
  const formatDeadline = (value) => {
    return formatDate(value, locale);
  };
  const activityKind = editingUsers?.length ? 'editing' : draggingUsers?.length ? 'moving' : null;
  const activityUsers = activityKind === 'editing' ? editingUsers : activityKind === 'moving' ? draggingUsers : [];
  const activityLabel = activityKind ? getPresenceLabel(activityKind, activityUsers.length, locale) : null;

  return (
    <>
      {activityUsers.length > 0 && activityLabel ? (
        <ActivityIndicator users={activityUsers} label={activityLabel} locale={locale} />
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
  const indicatorColor = isEditing
    ? editingUsers?.[0]?.color
    : isOtherDragging
      ? draggingUsers?.[0]?.color
      : 'transparent';

  return (
    <button
      ref={setNodeRef}
      type="button"
      className={`${styles.card} ${dragDisabled ? styles.cardStatic : ''} ${isDragging ? styles.dragging : ''} ${isEditing ? styles.cardEditing : ''} ${isOtherDragging ? styles.cardMoving : ''}`}
      style={{
        transform: CSS.Translate.toString(transform),
        transition,
        '--indicator-color': indicatorColor || 'transparent',
      }}
      onClick={() => onOpen(task)}
      {...attributes}
      {...listeners}
    >
      <TaskCardContent task={task} editingUsers={editingUsers} draggingUsers={draggingUsers} locale={language} />
    </button>
  );
}

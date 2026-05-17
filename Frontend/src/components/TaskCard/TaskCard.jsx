import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import Badge from '../Ui/Badge';
import styles from './TaskCard.module.css';

function getPriorityTone(priority) {
  if (priority === 'CRITICAL') return 'danger';
  if (priority === 'HIGH') return 'warning';
  return 'neutral';
}

function formatDeadline(value) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(value));
}

function TaskCardContent({ task, editingUsers, draggingUsers }) {
  return (
    <>
      <div className={styles.header}>
        <span className={styles.id}>#{task.id.slice(0, 8)}</span>
        <Badge tone={getPriorityTone(task.priority)}>{task.priority}</Badge>
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
        <span>{task.deadline ? formatDeadline(task.deadline) : 'No deadline'}</span>
      </div>
      
      {editingUsers?.length > 0 && (
         <div className={styles.indicatorBadge}>
            <span className={styles.indicatorDot} style={{backgroundColor: editingUsers[0].color}}></span>
            Editing by {editingUsers[0].display_name}
         </div>
      )}
      
      {draggingUsers?.length > 0 && !editingUsers?.length && (
         <div className={styles.indicatorBadge}>
            <span className={styles.indicatorDot} style={{backgroundColor: draggingUsers[0].color}}></span>
            Moving by {draggingUsers[0].display_name}
         </div>
      )}
    </>
  );
}

export function TaskCardPreview({ task }) {
  return (
    <div className={`${styles.card} ${styles.overlay}`}>
      <TaskCardContent task={task} />
    </div>
  );
}

export default function TaskCard({ task, onOpen, editingUsers, draggingUsers, dragDisabled = false }) {
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
      <TaskCardContent task={task} editingUsers={editingUsers} draggingUsers={draggingUsers} />
    </button>
  );
}

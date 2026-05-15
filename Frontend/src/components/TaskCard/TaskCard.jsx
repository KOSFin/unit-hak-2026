import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import Badge from '../Ui/Badge';
import styles from './TaskCard.module.css';

function getPriorityTone(priority) {
  if (priority === 'CRITICAL') return 'danger';
  if (priority === 'HIGH') return 'warning';
  return 'neutral';
}

export default function TaskCard({ task, onOpen }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `task:${task.id}`,
    data: {
      type: 'task',
      taskId: task.id,
      columnId: task.column_id,
    },
  });

  return (
    <button
      ref={setNodeRef}
      type="button"
      className={`${styles.card} ${isDragging ? styles.dragging : ''}`}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
      onClick={() => onOpen(task)}
      {...attributes}
      {...listeners}
    >
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
        <span>{task.deadline ? new Date(task.deadline).toLocaleDateString() : 'No deadline'}</span>
      </div>
    </button>
  );
}

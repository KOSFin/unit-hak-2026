import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';

import Button from '../Ui/Button';
import TaskCard from '../TaskCard/TaskCard';
import styles from './Column.module.css';

export default function Column({ column, tasks, onCreateTask, onOpenTask, editingUsersMap, draggingUsersMap }) {
  const { setNodeRef } = useDroppable({
    id: `column:${column.id}`,
    data: {
      type: 'column',
      columnId: column.id,
    },
  });

  return (
    <div className={styles.column}>
      <div className={styles.header}>
        <h2 className={styles.title}>{column.title}</h2>
        <span className={styles.counter}>{tasks.length}</span>
      </div>

      <div className={styles.list} ref={setNodeRef}>
        <SortableContext
          items={tasks.map((t) => `task:${t.id}`)}
          strategy={verticalListSortingStrategy}
        >
          {tasks.map((task) => (
            <TaskCard 
               key={task.id} 
               task={task} 
               onOpen={onOpenTask} 
               editingUsers={editingUsersMap?.[task.id]} 
               draggingUsers={draggingUsersMap?.[task.id]}
            />
          ))}
        </SortableContext>
      </div>

      <div className={styles.footer}>
        <Button variant="ghost" size="sm" onClick={() => onCreateTask(column.id)}>
          + Add task
        </Button>
      </div>
    </div>
  );
}

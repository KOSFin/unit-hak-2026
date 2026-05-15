import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useDroppable } from '@dnd-kit/core';

import Button from '../Ui/Button';
import TaskCard from '../TaskCard/TaskCard';
import styles from './Column.module.css';

export default function Column({ column, tasks, onCreateTask, onOpenTask }) {
  const { isOver, setNodeRef } = useDroppable({
    id: `column:${column.id}`,
    data: {
      type: 'column',
      columnId: column.id,
    },
  });

  return (
    <section ref={setNodeRef} className={`${styles.column} ${isOver ? styles.over : ''}`}>
      <header className={styles.header}>
        <div>
          <p className={styles.kicker}>{column.is_default ? 'Default lane' : 'Custom lane'}</p>
          <h2 className={styles.title}>{column.title}</h2>
        </div>
        <span className={styles.count}>{tasks.length}</span>
      </header>

      <SortableContext
        items={tasks.map((task) => `task:${task.id}`)}
        strategy={verticalListSortingStrategy}
      >
        <div className={styles.list}>
          {tasks.length === 0 ? <div className={styles.empty}>Drop a task here</div> : null}
          {tasks.map((task) => (
            <TaskCard key={task.id} task={task} onOpen={onOpenTask} />
          ))}
        </div>
      </SortableContext>

      <Button variant="ghost" block onClick={() => onCreateTask(column.id)}>
        Add task
      </Button>
    </section>
  );
}

import { DndContext, PointerSensor, closestCorners, useSensor, useSensors } from '@dnd-kit/core';

import Column from '../Column/Column';
import styles from './Board.module.css';

export default function Board({
  columns,
  tasks,
  onCreateTask,
  onOpenTask,
  onMoveTask,
}) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
  );

  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) {
      return;
    }

    const activeTaskId = String(active.id).replace('task:', '');
    const activeTask = tasks.find((task) => task.id === activeTaskId);

    if (!activeTask) {
      return;
    }

    let targetColumnId = null;
    const overId = String(over.id);
    if (overId.startsWith('column:')) {
      targetColumnId = overId.replace('column:', '');
    }

    if (overId.startsWith('task:')) {
      targetColumnId = tasks.find((task) => task.id === overId.replace('task:', ''))?.column_id ?? null;
    }

    if (!targetColumnId || targetColumnId === activeTask.column_id) {
      return;
    }

    const nextPosition = tasks.filter((task) => task.column_id === targetColumnId).length + 1;
    onMoveTask(activeTask, targetColumnId, nextPosition);
  };

  return (
    <DndContext sensors={sensors} collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
      <div className={styles.board}>
        {columns.map((column) => (
          <Column
            key={column.id}
            column={column}
            tasks={tasks.filter((task) => task.column_id === column.id)}
            onCreateTask={onCreateTask}
            onOpenTask={onOpenTask}
          />
        ))}
      </div>
    </DndContext>
  );
}

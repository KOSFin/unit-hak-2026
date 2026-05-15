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
        distance: 4,
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
    let targetIndex = 0;
    const overId = String(over.id);

    if (overId.startsWith('task:')) {
      const overTaskId = overId.replace('task:', '');
      const overTask = tasks.find((task) => task.id === overTaskId);
      if (!overTask) {
        return;
      }
      targetColumnId = overTask.column_id;
      const columnTasks = tasks.filter((task) => task.column_id === targetColumnId);
      targetIndex = columnTasks.findIndex((task) => task.id === overTaskId);
    } else if (overId.startsWith('column:')) {
      targetColumnId = overId.replace('column:', '');
      targetIndex = tasks.filter((task) => task.column_id === targetColumnId).length;
    }

    if (!targetColumnId) {
      return;
    }

    const sourceIndex = tasks
      .filter((task) => task.column_id === activeTask.column_id)
      .findIndex((task) => task.id === activeTaskId);
    if (targetColumnId === activeTask.column_id && targetIndex === sourceIndex) {
      return;
    }

    onMoveTask(activeTask, targetColumnId, targetIndex);
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

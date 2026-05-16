import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useEffect, useMemo, useRef, useState } from 'react';

import Column from '../Column/Column';
import { TaskCardPreview } from '../TaskCard/TaskCard';
import { reorderTasks } from '../../utils/reorderTasks';
import styles from './Board.module.css';

export default function Board({
  columns,
  tasks,
  onCreateTask,
  onOpenTask,
  onMoveTask,
}) {
  const [activeId, setActiveId] = useState(null);
  const [localTasks, setLocalTasks] = useState(tasks);
  const ignoreSyncRef = useRef(false);
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 4,
      },
    }),
  );

  useEffect(() => {
    if (!activeId) {
      if (ignoreSyncRef.current) {
        ignoreSyncRef.current = false;
        return;
      }
      setLocalTasks(tasks);
    }
  }, [tasks, activeId]);

  const activeTask = useMemo(() => {
    if (!activeId) {
      return null;
    }
    const activeTaskId = String(activeId).replace('task:', '');
    return localTasks.find((task) => task.id === activeTaskId) ?? null;
  }, [activeId, localTasks]);

  const getDropTarget = (over, currentTasks) => {
    if (!over) {
      return null;
    }

    const overId = String(over.id);
    if (overId.startsWith('task:')) {
      const overTaskId = overId.replace('task:', '');
      const overTask = currentTasks.find((task) => task.id === overTaskId);
      if (!overTask) {
        return null;
      }
      const columnTasks = currentTasks.filter((task) => task.column_id === overTask.column_id);
      const targetIndex = columnTasks.findIndex((task) => task.id === overTaskId);
      return { targetColumnId: overTask.column_id, targetIndex };
    }

    if (overId.startsWith('column:')) {
      const targetColumnId = overId.replace('column:', '');
      const targetIndex = currentTasks.filter((task) => task.column_id === targetColumnId)
        .length;
      return { targetColumnId, targetIndex };
    }

    return null;
  };

  const handleDragStart = ({ active }) => {
    setActiveId(active.id);
    setLocalTasks(tasks);
  };

  const handleDragOver = ({ active, over }) => {
    if (!over || active.id === over.id) {
      return;
    }

    const activeTaskId = String(active.id).replace('task:', '');
    const activeTask = localTasks.find((task) => task.id === activeTaskId);
    if (!activeTask) {
      return;
    }

    const dropTarget = getDropTarget(over, localTasks);
    if (!dropTarget) {
      return;
    }

    const { targetColumnId, targetIndex } = dropTarget;
    const sourceIndex = localTasks
      .filter((task) => task.column_id === activeTask.column_id)
      .findIndex((task) => task.id === activeTaskId);
    if (targetColumnId === activeTask.column_id && targetIndex === sourceIndex) {
      return;
    }

    setLocalTasks(reorderTasks(localTasks, columns, activeTaskId, targetColumnId, targetIndex));
  };

  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    const activeTaskId = String(active.id).replace('task:', '');
    const activeTask = localTasks.find((task) => task.id === activeTaskId);

    if (!activeTask) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    const dropTarget = getDropTarget(over, localTasks);
    if (!dropTarget) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    const { targetColumnId, targetIndex } = dropTarget;

    const sourceIndex = localTasks
      .filter((task) => task.column_id === activeTask.column_id)
      .findIndex((task) => task.id === activeTaskId);
    if (targetColumnId === activeTask.column_id && targetIndex === sourceIndex) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    ignoreSyncRef.current = true;
    setLocalTasks(reorderTasks(localTasks, columns, activeTaskId, targetColumnId, targetIndex));
    setActiveId(null);
    onMoveTask(activeTask, targetColumnId, targetIndex);
  };

  const handleDragCancel = () => {
    setActiveId(null);
    setLocalTasks(tasks);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className={styles.board}>
        {columns.map((column) => (
          <Column
            key={column.id}
            column={column}
            tasks={localTasks.filter((task) => task.column_id === column.id)}
            onCreateTask={onCreateTask}
            onOpenTask={onOpenTask}
          />
        ))}
      </div>
      <DragOverlay
        dropAnimation={{
          duration: 220,
          easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
        }}
      >
        {activeTask ? <TaskCardPreview task={activeTask} /> : null}
      </DragOverlay>
    </DndContext>
  );
}

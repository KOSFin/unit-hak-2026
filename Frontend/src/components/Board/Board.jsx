import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

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
  editingUsersMap = {},
  draggingUsersMap = {},
  onDragStartEmit,
  onDragEndEmit,
  dragDisabled = false,
}) {
  const [activeId, setActiveId] = useState(null);
  const [localTasks, setLocalTasks] = useState(tasks);
  const dragStartTasksRef = useRef(null);
  const ignoreSyncRef = useRef(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 6,
      },
    }),
  );

  useEffect(() => {
    if (activeId !== null) return;
    if (ignoreSyncRef.current) {
      ignoreSyncRef.current = false;
      return;
    }
    setLocalTasks(tasks);
  }, [tasks, activeId]);

  const [activeTaskSnapshot, setActiveTaskSnapshot] = useState(null);

  const activeTask = useMemo(() => {
    if (!activeId) return null;
    const id = String(activeId).replace('task:', '');
    return activeTaskSnapshot ?? localTasks.find((t) => t.id === id) ?? null;
  }, [activeId, localTasks, activeTaskSnapshot]);

  const handleDragStart = useCallback(({ active }) => {
    dragStartTasksRef.current = localTasks;
    const id = String(active.id).replace('task:', '');
    const taskObj = localTasks.find(t => t.id === id);
    setActiveTaskSnapshot(taskObj ?? null);
    setActiveId(active.id);
    if (onDragStartEmit && taskObj) {
      onDragStartEmit(taskObj.id);
    }
  }, [localTasks, onDragStartEmit]);

  const handleDragOver = useCallback(({ active, over }) => {
    if (!over || active.id === over.id) return;

    const activeIdStr = String(active.id).replace('task:', '');
    const overIdStr = String(over.id).replace('task:', '').replace('column:', '');

    setLocalTasks((prev) => {
      const activeTask = prev.find((t) => t.id === activeIdStr);
      if (!activeTask) return prev;

      const isOverColumn = String(over.id).startsWith('column:');
      
      let targetColumnId;
      if (isOverColumn) {
        targetColumnId = overIdStr;
      } else {
        const overTask = prev.find((t) => t.id === overIdStr);
        if (!overTask) return prev;
        targetColumnId = overTask.column_id;
      }

      if (activeTask.column_id === targetColumnId) {
        return prev;
      }

      let targetIndex;
      if (isOverColumn) {
        targetIndex = prev.filter((t) => t.column_id === targetColumnId).length;
      } else {
        const columnTasks = prev.filter((t) => t.column_id === targetColumnId);
        targetIndex = columnTasks.findIndex((t) => t.id === overIdStr);

        const overRect = over.rect;
        if (overRect && active.rect?.current?.translated) {
          const overMidY = overRect.top + overRect.height / 2;
          const activeCenterY =
            active.rect.current.translated.top + active.rect.current.translated.height / 2;
          if (activeCenterY > overMidY) {
            targetIndex += 1;
          }
        }
      }

      return reorderTasks(prev, columns, activeIdStr, targetColumnId, targetIndex);
    });
  }, [columns]);

  const handleDragEnd = useCallback(({ active, over }) => {
    const snapshot = dragStartTasksRef.current;
    dragStartTasksRef.current = null;
    
    if (onDragEndEmit) {
      onDragEndEmit();
    }

    if (!over || !snapshot) {
      setActiveTaskSnapshot(null);
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    const activeIdStr = String(active.id).replace('task:', '');
    const overIdStr = String(over.id).replace('task:', '').replace('column:', '');

    const activeTaskOriginal = snapshot.find((t) => t.id === activeIdStr);
    if (!activeTaskOriginal) {
        setActiveTaskSnapshot(null);
        setActiveId(null);
        setLocalTasks(tasks);
        return;
    }

    setLocalTasks((currentTasks) => {
      setActiveTaskSnapshot(null);
      const activeTaskCurrent = currentTasks.find((t) => t.id === activeIdStr);
      if (!activeTaskCurrent) {
        setActiveId(null);
        return tasks;
      }

      const isOverColumn = String(over.id).startsWith('column:');
      let targetColumnId;
      if (isOverColumn) {
        targetColumnId = overIdStr;
      } else {
        const overTask = currentTasks.find((t) => t.id === overIdStr);
        if (!overTask) {
           setActiveId(null);
           return tasks;
        }
        targetColumnId = overTask.column_id;
      }

      let targetIndex;
      const columnTasks = currentTasks.filter((t) => t.column_id === targetColumnId);
      
      if (isOverColumn) {
          targetIndex = columnTasks.length;
          if (activeTaskCurrent.column_id === targetColumnId) {
             targetIndex = Math.max(0, targetIndex - 1);
          }
      } else {
          targetIndex = columnTasks.findIndex((t) => t.id === overIdStr);

          if (activeTaskCurrent.column_id !== targetColumnId) {
             const overRect = over.rect;
             if (overRect && active.rect?.current?.translated) {
               const overMidY = overRect.top + overRect.height / 2;
               const activeCenterY =
                 active.rect.current.translated.top + active.rect.current.translated.height / 2;
               if (activeCenterY > overMidY) {
                 targetIndex += 1;
               }
             }
          }
      }

      const finalTasks = reorderTasks(currentTasks, columns, activeIdStr, targetColumnId, targetIndex);
      
      const noChange =
        targetColumnId === activeTaskOriginal.column_id &&
        targetIndex === snapshot.filter(t => t.column_id === targetColumnId).findIndex(t => t.id === activeIdStr);

      if (noChange) {
        setActiveId(null);
        return tasks;
      }

      ignoreSyncRef.current = true;
      setActiveId(null);
      
      const finalColumnTasks = finalTasks.filter(t => t.column_id === targetColumnId);
      const finalIndex = finalColumnTasks.findIndex(t => t.id === activeIdStr);

      setTimeout(() => {
         onMoveTask(activeTaskOriginal, targetColumnId, finalIndex);
      }, 0);

      return finalTasks;
    });
  }, [columns, tasks, onMoveTask, onDragEndEmit]);

  const handleDragCancel = useCallback(() => {
    dragStartTasksRef.current = null;
    setActiveTaskSnapshot(null);
    setActiveId(null);
    setLocalTasks(tasks);
    if (onDragEndEmit) {
      onDragEndEmit();
    }
  }, [tasks, onDragEndEmit]);

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
            editingUsersMap={editingUsersMap}
            draggingUsersMap={draggingUsersMap}
            dragDisabled={dragDisabled}
          />
        ))}
      </div>
      <DragOverlay
        dropAnimation={{
          duration: 200,
          easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
        }}
      >
        {activeTask ? <TaskCardPreview task={activeTask} /> : null}
      </DragOverlay>
    </DndContext>
  );
}

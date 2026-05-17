import {
  DndContext,
  DragOverlay,
  PointerSensor,
  closestCorners,
  pointerWithin,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import Column from '../Column/Column';
import { TaskCardPreview } from '../TaskCard/TaskCard';
import { reorderTasks } from '../../utils/reorderTasks';
import styles from './Board.module.css';

function isTaskContainer(container) {
  return container?.data?.current?.type === 'task';
}

function isColumnContainer(container) {
  return container?.data?.current?.type === 'column';
}

function getClosestTaskCollisions(args, columnId = null) {
  const taskContainers = args.droppableContainers.filter((container) => {
    if (!isTaskContainer(container)) {
      return false;
    }

    if (!columnId) {
      return true;
    }

    return container.data.current?.columnId === columnId;
  });

  if (taskContainers.length === 0) {
    return [];
  }

  return closestCorners({
    ...args,
    droppableContainers: taskContainers,
  });
}

function collisionDetectionStrategy(args) {
  const pointerCollisions = pointerWithin(args);
  const taskPointerCollisions = pointerCollisions.filter(({ id }) => String(id).startsWith('task:'));
  if (taskPointerCollisions.length > 0) {
    return taskPointerCollisions;
  }

  const hoveredColumn = pointerCollisions.find(({ id }) => String(id).startsWith('column:'));
  if (hoveredColumn) {
    const hoveredColumnId = String(hoveredColumn.id).replace('column:', '');
    const columnTaskCollisions = getClosestTaskCollisions(args, hoveredColumnId);
    if (columnTaskCollisions.length > 0) {
      return columnTaskCollisions;
    }

    return [hoveredColumn];
  }

  const taskCollisions = getClosestTaskCollisions(args);
  if (taskCollisions.length > 0) {
    return taskCollisions;
  }

  return closestCorners({
    ...args,
    droppableContainers: args.droppableContainers.filter(isColumnContainer),
  });
}

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

  const getSortedColumnTasks = useCallback(
    (taskList, columnId) =>
      taskList
        .filter((task) => task.column_id === columnId)
        .sort((left, right) => (left.position ?? 0) - (right.position ?? 0)),
    [],
  );

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

      let targetIndex;
      if (isOverColumn) {
        targetIndex = getSortedColumnTasks(prev, targetColumnId).length;
      } else {
        const columnTasks = getSortedColumnTasks(prev, targetColumnId);
        targetIndex = columnTasks.findIndex((t) => t.id === overIdStr);
        if (targetIndex === -1) {
          return prev;
        }

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
  }, [columns, getSortedColumnTasks]);

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

      const targetColumnId = activeTaskCurrent.column_id;
      const finalColumnTasks = getSortedColumnTasks(currentTasks, targetColumnId);
      const finalIndex = finalColumnTasks.findIndex((task) => task.id === activeIdStr);
      if (finalIndex === -1) {
        setActiveId(null);
        return tasks;
      }

      const originalColumnTasks = getSortedColumnTasks(snapshot, activeTaskOriginal.column_id);
      const originalIndex = originalColumnTasks.findIndex((task) => task.id === activeIdStr);
      const noChange =
        targetColumnId === activeTaskOriginal.column_id &&
        finalIndex === originalIndex;

      if (noChange) {
        setActiveId(null);
        return tasks;
      }

      ignoreSyncRef.current = true;
      setActiveId(null);

      setTimeout(() => {
         onMoveTask(activeTaskOriginal, targetColumnId, finalIndex);
      }, 0);

      return currentTasks;
    });
  }, [getSortedColumnTasks, tasks, onMoveTask, onDragEndEmit]);

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
      collisionDetection={collisionDetectionStrategy}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className={styles.board}>
        {columns.map((column) => {
          const columnTasks = localTasks
            .filter((task) => task.column_id === column.id)
            .sort((a, b) => (a.position ?? 0) - (b.position ?? 0));
          
          return (
            <Column
              key={column.id}
              column={column}
              tasks={columnTasks}
              onCreateTask={onCreateTask}
              onOpenTask={onOpenTask}
              editingUsersMap={editingUsersMap}
              draggingUsersMap={draggingUsersMap}
              dragDisabled={dragDisabled}
            />
          );
        })}
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

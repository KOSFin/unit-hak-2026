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
}) {
  // localTasks is the optimistic view during drag and the committed view after
  const [activeId, setActiveId] = useState(null);
  const [localTasks, setLocalTasks] = useState(tasks);

  // Snapshot of tasks at the moment drag started — never mutated during drag
  const dragStartTasksRef = useRef(null);
  // True while we are suppressing the next server-sync (right after we commit a move)
  const ignoreSyncRef = useRef(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        // Require a small movement to distinguish drag from click
        distance: 6,
      },
    }),
  );

  const collisionDetection = useCallback((args) => {
    const collisions = closestCorners(args);
    const nonActive = collisions.filter((collision) => collision.id !== args.active.id);
    const candidates = nonActive.length ? nonActive : collisions;
    const taskCollisions = candidates.filter((collision) =>
      String(collision.id).startsWith('task:'),
    );
    return taskCollisions.length ? taskCollisions : candidates;
  }, []);

  // Sync server state → localTasks only when NOT dragging and not suppressed
  useEffect(() => {
    if (activeId !== null) {
      // Mid-drag: never overwrite optimistic state with server data
      return;
    }
    if (ignoreSyncRef.current) {
      ignoreSyncRef.current = false;
      return;
    }
    setLocalTasks(tasks);
  }, [tasks, activeId]);

  const activeTask = useMemo(() => {
    if (!activeId) return null;
    const id = String(activeId).replace('task:', '');
    // Look up in the drag-start snapshot so the overlay never "jumps"
    return (dragStartTasksRef.current ?? localTasks).find((t) => t.id === id) ?? null;
  }, [activeId, localTasks]);

  /**
   * Given the droppable `over` and the active draggable descriptor, compute
   * where the card should land.
   *
   * IMPORTANT: we always compute indices relative to `snapshot` (the task list
   * at drag-start), not the live optimistic list.  This prevents accumulated
   * errors when DragOver fires many times per second.
   */
  const resolveDropTarget = useCallback((over, active, snapshot) => {
    if (!over) return null;

    const activeTaskId = String(active.id).replace('task:', '');
    const activeTask = snapshot.find((task) => task.id === activeTaskId);
    const sourceColumnId = activeTask?.column_id ?? null;
    const sourceColumnTasks = sourceColumnId
      ? snapshot.filter((task) => task.column_id === sourceColumnId)
      : [];
    const sourceIndex = sourceColumnTasks.findIndex((task) => task.id === activeTaskId);

    const overId = String(over.id);

    if (overId.startsWith('task:')) {
      const overTaskId = overId.replace('task:', '');
      const overTask = snapshot.find((t) => t.id === overTaskId);
      if (!overTask) return null;

      const columnTasks = snapshot.filter((t) => t.column_id === overTask.column_id);
      let targetIndex = columnTasks.findIndex((t) => t.id === overTaskId);

      // Insert *after* the hovered card when the dragged card's centre is below the hovered card's centre
      if (over.rect && active.rect?.current?.translated) {
        const overMidY = over.rect.top + over.rect.height / 2;
        const activeCenterY =
          active.rect.current.translated.top + active.rect.current.translated.height / 2;
        if (activeCenterY > overMidY) {
          targetIndex += 1;
        }
      }

      if (sourceColumnId === overTask.column_id && sourceIndex !== -1 && sourceIndex < targetIndex) {
        targetIndex -= 1;
      }

      return { targetColumnId: overTask.column_id, targetIndex };
    }

    if (overId.startsWith('column:')) {
      const targetColumnId = overId.replace('column:', '');
      // Append to the end of the column
      let targetIndex = snapshot.filter((t) => t.column_id === targetColumnId).length;
      if (sourceColumnId === targetColumnId && sourceIndex !== -1) {
        targetIndex = Math.max(0, targetIndex - 1);
      }
      return { targetColumnId, targetIndex };
    }

    return null;
  }, []);

  const handleDragStart = useCallback(({ active }) => {
    // Take a clean snapshot before any optimistic updates
    dragStartTasksRef.current = localTasks;
    setActiveId(active.id);
  }, [localTasks]);

  const handleDragOver = useCallback(({ active, over }) => {
    if (!over || active.id === over.id) return;

    const snapshot = dragStartTasksRef.current;
    if (!snapshot) return;

    const activeTaskId = String(active.id).replace('task:', '');

    const dropTarget = resolveDropTarget(over, active, snapshot);
    if (!dropTarget) return;

    const { targetColumnId, targetIndex } = dropTarget;

    // Apply optimistic reorder against the snapshot so each DragOver event
    // produces a clean result instead of accumulating tiny errors
    const optimistic = reorderTasks(snapshot, columns, activeTaskId, targetColumnId, targetIndex);
    setLocalTasks(optimistic);
  }, [columns, resolveDropTarget]);

  const handleDragEnd = useCallback(({ active, over }) => {
    const snapshot = dragStartTasksRef.current;
    dragStartTasksRef.current = null;

    if (!over || !snapshot) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    const activeTaskId = String(active.id).replace('task:', '');

    // Resolve against the SNAPSHOT so the index matches what the server expects
    const dropTarget = resolveDropTarget(over, active, snapshot);
    if (!dropTarget) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    const { targetColumnId, targetIndex } = dropTarget;

    // Check if the card actually moved
    const originalTask = snapshot.find((t) => t.id === activeTaskId);
    const originalColumnTasks = snapshot.filter((t) => t.column_id === targetColumnId);
    const originalIndex = originalColumnTasks.findIndex((t) => t.id === activeTaskId);
    const noChange =
      originalTask &&
      targetColumnId === originalTask.column_id &&
      targetIndex === originalIndex;

    if (noChange) {
      setActiveId(null);
      setLocalTasks(tasks);
      return;
    }

    // Commit optimistic state for the final position
    const finalTasks = reorderTasks(snapshot, columns, activeTaskId, targetColumnId, targetIndex);
    ignoreSyncRef.current = true;
    setLocalTasks(finalTasks);
    setActiveId(null);

    // activeTask must be fetched from snapshot (task object carries version, etc.)
    const activeTask = snapshot.find((t) => t.id === activeTaskId);
    if (activeTask) {
      onMoveTask(activeTask, targetColumnId, targetIndex);
    }
  }, [columns, tasks, resolveDropTarget, onMoveTask]);

  const handleDragCancel = useCallback(() => {
    dragStartTasksRef.current = null;
    setActiveId(null);
    setLocalTasks(tasks);
  }, [tasks]);

  return (
    <DndContext
      sensors={sensors}
      // Prefer task collisions so we can reliably drop at any index
      collisionDetection={collisionDetection}
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
          duration: 200,
          easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
        }}
      >
        {activeTask ? <TaskCardPreview task={activeTask} /> : null}
      </DragOverlay>
    </DndContext>
  );
}

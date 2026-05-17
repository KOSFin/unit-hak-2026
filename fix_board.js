const fs = require('fs');

const path = 'Frontend/src/components/Board/Board.jsx';
let content = fs.readFileSync(path, 'utf8');

// Replace handleDragOver
content = content.replace(/const handleDragOver = useCallback[\s\S]*?\}, \[columns, getSortedColumnTasks\]\);/, `const handleDragOver = useCallback(({ active, over }) => {
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
        targetIndex = getSortedColumnTasks(prev, targetColumnId).length;
      } else {
        const columnTasks = getSortedColumnTasks(prev, targetColumnId);
        targetIndex = columnTasks.findIndex((t) => t.id === overIdStr);
        if (targetIndex !== -1) {
          const overRect = over.rect;
          if (overRect && active.rect?.current?.translated) {
            const overMidY = overRect.top + overRect.height / 2;
            const activeCenterY =
              active.rect.current.translated.top + active.rect.current.translated.height / 2;
            if (activeCenterY > overMidY) {
              targetIndex += 1;
            }
          }
        } else {
           targetIndex = 0;
        }
      }

      return reorderTasks(prev, columns, activeIdStr, targetColumnId, targetIndex);
    });
  }, [columns, getSortedColumnTasks]);`);

// Replace handleDragEnd
content = content.replace(/const handleDragEnd = useCallback[\s\S]*?\}, \[getSortedColumnTasks, tasks, onMoveTask, onDragEndEmit\]\);/, `const handleDragEnd = useCallback(({ active, over }) => {
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

      const isOverColumn = String(over.id).startsWith('column:');
      const overIdStr = String(over.id).replace('task:', '').replace('column:', '');

      let targetColumnId;
      if (isOverColumn) {
        targetColumnId = overIdStr;
      } else {
        const overTaskCurrent = currentTasks.find((t) => t.id === overIdStr);
        targetColumnId = overTaskCurrent ? overTaskCurrent.column_id : activeTaskCurrent.column_id;
      }

      let finalTasks = currentTasks;

      if (active.id !== over.id && !isOverColumn) {
         if (activeTaskCurrent.column_id === targetColumnId) {
             const columnTasks = getSortedColumnTasks(currentTasks, targetColumnId);
             const activeIndex = columnTasks.findIndex(t => t.id === activeIdStr);
             const overIndex = columnTasks.findIndex(t => t.id === overIdStr);
             
             if (activeIndex !== overIndex && overIndex !== -1) {
                 finalTasks = reorderTasks(currentTasks, columns, activeIdStr, targetColumnId, overIndex);
             }
         }
      } else if (isOverColumn && activeTaskCurrent.column_id !== targetColumnId) {
           const columnTasks = getSortedColumnTasks(currentTasks, targetColumnId);
           finalTasks = reorderTasks(currentTasks, columns, activeIdStr, targetColumnId, columnTasks.length);
      }

      const finalColumnTasks = getSortedColumnTasks(finalTasks, targetColumnId);
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
        return finalTasks;
      }

      ignoreSyncRef.current = true;
      setActiveId(null);

      setTimeout(() => {
         onMoveTask(activeTaskOriginal, targetColumnId, finalIndex);
      }, 0);

      return finalTasks;
    });
  }, [getSortedColumnTasks, tasks, onMoveTask, onDragEndEmit, columns]);`);

fs.writeFileSync(path, content, 'utf8');

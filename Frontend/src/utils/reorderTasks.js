export function reorderTasks(tasks, columns, taskId, targetColumnId, targetIndex) {
  const columnOrder = columns?.map((column) => column.id) ?? [];
  const buckets = new Map(columnOrder.map((columnId) => [columnId, []]));

  tasks.forEach((task) => {
    if (!buckets.has(task.column_id)) {
      buckets.set(task.column_id, []);
    }
    buckets.get(task.column_id).push(task);
  });

  let movingTask = null;
  let sourceColumnId = null;
  buckets.forEach((list, columnId) => {
    const index = list.findIndex((item) => item.id === taskId);
    if (index !== -1) {
      movingTask = list[index];
      sourceColumnId = columnId;
      list.splice(index, 1);
    }
  });

  if (!movingTask) {
    return tasks;
  }

  const targetList = buckets.get(targetColumnId) ?? [];
  const clampedIndex = Math.max(0, Math.min(targetIndex, targetList.length));
  targetList.splice(clampedIndex, 0, { ...movingTask, column_id: targetColumnId });
  buckets.set(targetColumnId, targetList);

  const rebuildColumn = (columnId) => {
    const list = buckets.get(columnId) ?? [];
    return list.map((item, index) => ({ ...item, position: index + 1 }));
  };

  const updatedColumns = new Set([sourceColumnId, targetColumnId]);
  const result = [];
  columnOrder.forEach((columnId) => {
    if (updatedColumns.has(columnId)) {
      result.push(...rebuildColumn(columnId));
    } else {
      result.push(...(buckets.get(columnId) ?? []));
    }
  });

  buckets.forEach((list, columnId) => {
    if (!columnOrder.includes(columnId)) {
      result.push(...list.map((item, index) => ({ ...item, position: index + 1 })));
    }
  });

  return result;
}

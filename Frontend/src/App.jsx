import { useCallback, useEffect, useRef, useState } from 'react';

import { getErrorMessage } from './api/client';
import { createColumn, deleteColumn, updateColumn } from './api/columnsApi';
import { getDefaultBoard } from './api/boardsApi';
import { createIncomingTask, getIncomingTasks } from './api/incomingTasksApi';
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from './api/notificationsApi';
import { createRule, deleteRule, getRules, updateRule } from './api/rulesApi';
import {
  createTask,
  deleteTask,
  getTasks,
  moveTask,
  updateTask,
} from './api/tasksApi';
import AdminPanel from './components/AdminPanel/AdminPanel';
import Board from './components/Board/Board';
import Layout from './components/Layout/Layout';
import TaskModal from './components/TaskModal/TaskModal';
import Modal from './components/Ui/Modal';
import Toast from './components/Ui/Toast';
import { createRealtimeSocket } from './realtime/socket';

function sortColumns(columns) {
  return [...columns].sort((left, right) => left.position - right.position);
}

function sortTasks(tasks) {
  return [...tasks].sort((left, right) => left.position - right.position);
}

function reorderTasks(tasks, columns, taskId, targetColumnId, targetIndex) {
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

export default function App() {
  const [board, setBoard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [rules, setRules] = useState([]);
  const [incomingTasks, setIncomingTasks] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [modalState, setModalState] = useState({
    open: false,
    task: null,
    columnId: null,
  });
  const [toast, setToast] = useState(null);
  const toastTimeoutRef = useRef(null);
  const previousConnectionRef = useRef(connectionStatus);

  const showToast = (message, tone = 'neutral') => {
    if (toastTimeoutRef.current) {
      window.clearTimeout(toastTimeoutRef.current);
    }

    setToast({ message, tone });
    toastTimeoutRef.current = window.setTimeout(() => {
      setToast(null);
    }, 3200);
  };

  const loadBoard = useCallback(async () => {
    const boardData = await getDefaultBoard();
    const taskData = await getTasks(boardData.id);
    setBoard({
      ...boardData,
      columns: sortColumns(boardData.columns),
    });
    setTasks(sortTasks(taskData));
  }, []);

  const loadNotifications = useCallback(async () => {
    setNotifications(await getNotifications());
  }, []);

  const loadRules = useCallback(async () => {
    setRules(await getRules());
  }, []);

  const loadIncomingTasks = useCallback(async () => {
    setIncomingTasks(await getIncomingTasks());
  }, []);

  const loadAll = useCallback(async () => {
    try {
      setLoading(true);
      await loadBoard();
      await Promise.all([loadNotifications(), loadRules(), loadIncomingTasks()]);
    } catch (error) {
      showToast(getErrorMessage(error, 'Failed to load FlowBoard'), 'danger');
    } finally {
      setLoading(false);
    }
  }, [loadBoard, loadIncomingTasks, loadNotifications, loadRules]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAll();
    }, 0);

    return () => {
      window.clearTimeout(timer);
      if (toastTimeoutRef.current) {
        window.clearTimeout(toastTimeoutRef.current);
      }
    };
  }, [loadAll]);

  useEffect(() => {
    if (!board?.id) {
      return undefined;
    }

    const socket = createRealtimeSocket({
      onOpen: () => setConnectionStatus('live'),
      onClose: () => setConnectionStatus('offline'),
      onError: () => setConnectionStatus('offline'),
      onMessage: async (event) => {
        if (event.type.startsWith('task.') || event.type === 'automation.triggered') {
          await loadBoard();
        }

        if (
          event.type === 'notification.created' ||
          event.type === 'automation.triggered' ||
          event.type === 'incoming-task.processed'
        ) {
          await loadNotifications();
        }

        if (event.type === 'incoming-task.processed') {
          await Promise.all([loadBoard(), loadIncomingTasks()]);
        }
      },
    });

    return () => {
      socket.close();
    };
  }, [board?.id, loadBoard, loadIncomingTasks, loadNotifications]);

  useEffect(() => {
    if (previousConnectionRef.current !== connectionStatus) {
      if (connectionStatus === 'offline') {
        showToast('Realtime connection lost. Reconnecting...', 'danger');
      }
      previousConnectionRef.current = connectionStatus;
    }
  }, [connectionStatus]);

  const runAction = async (action, successMessage) => {
    try {
      setBusy(true);
      await action();
      if (successMessage) {
        showToast(successMessage, 'success');
      }
    } catch (error) {
      showToast(getErrorMessage(error), 'danger');
    } finally {
      setBusy(false);
    }
  };

  const handleTaskSubmit = async (payload) => {
    await runAction(async () => {
      if (modalState.task) {
        await updateTask(modalState.task.id, {
          ...payload,
          version: modalState.task.version,
        });
      } else {
        await createTask({
          ...payload,
          column_id: modalState.columnId ?? payload.column_id,
        });
      }

      await loadBoard();
      setModalState({ open: false, task: null, columnId: null });
    }, modalState.task ? 'Task updated' : 'Task created');
  };

  const handleTaskDelete = async (task) => {
    await runAction(async () => {
      await deleteTask(task.id);
      await loadBoard();
      setModalState({ open: false, task: null, columnId: null });
    }, 'Task deleted');
  };

  const handleMoveTask = async (task, targetColumnId, targetIndex) => {
    if (!board?.columns?.length) {
      return;
    }

    const previousTasks = tasks;
    const nextTasks = reorderTasks(tasks, board.columns, task.id, targetColumnId, targetIndex);
    setTasks(nextTasks);

    try {
      setBusy(true);
      await moveTask(task.id, {
        column_id: targetColumnId,
        position: targetIndex + 1,
        version: task.version,
      });
      await loadBoard();
    } catch (error) {
      setTasks(previousTasks);
      showToast(getErrorMessage(error), 'danger');
    } finally {
      setBusy(false);
    }
  };

  const handleCreateColumn = async (title) => {
    await runAction(async () => {
      await createColumn({
        board_id: board.id,
        title,
      });
      await loadBoard();
    }, 'Column created');
  };

  const handleRenameColumn = async (columnId, title) => {
    await runAction(async () => {
      await updateColumn(columnId, { title });
      await loadBoard();
    }, 'Column updated');
  };

  const handleDeleteColumn = async (columnId) => {
    await runAction(async () => {
      await deleteColumn(columnId);
      await loadBoard();
    }, 'Column deleted');
  };

  const handleCreateRule = async (payload) => {
    await runAction(async () => {
      await createRule(payload);
      await loadRules();
    }, 'Automation rule created');
  };

  const handleToggleRule = async (rule) => {
    await runAction(async () => {
      await updateRule(rule.id, { enabled: !rule.enabled });
      await loadRules();
    }, 'Automation rule updated');
  };

  const handleDeleteRule = async (ruleId) => {
    await runAction(async () => {
      await deleteRule(ruleId);
      await loadRules();
    }, 'Automation rule deleted');
  };

  const handleSendDemoTask = async () => {
    await runAction(async () => {
      await createIncomingTask({
        external_id: `demo-${Date.now()}`,
        raw_payload: {
          title: 'Hackathon intake task',
          description: 'Generated from the FlowBoard admin panel.',
          tags: ['urgent', 'from-panel'],
        },
      });
      await loadIncomingTasks();
    }, 'Incoming task submitted');
  };

  const handleMarkNotificationRead = async (notificationId) => {
    await runAction(async () => {
      await markNotificationRead(notificationId);
      await loadNotifications();
    });
  };

  const handleMarkAllNotificationsRead = async () => {
    await runAction(async () => {
      await markAllNotificationsRead();
      await loadNotifications();
    }, 'Notifications cleared');
  };

  return (
    <>
      <Layout
        boardName={board?.name}
        notifications={notifications}
        notificationsOpen={notificationsOpen}
        pending={busy}
        onToggleNotifications={() => setNotificationsOpen((current) => !current)}
        onCloseNotifications={() => setNotificationsOpen(false)}
        onMarkNotificationRead={handleMarkNotificationRead}
        onMarkAllNotificationsRead={handleMarkAllNotificationsRead}
        onOpenAdmin={() => {
          setAdminOpen(true);
          setNotificationsOpen(false);
        }}
        onCreateTask={() =>
          setModalState({ open: true, task: null, columnId: board?.columns?.[0]?.id ?? null })
        }
      >
        {loading ? (
          <div>Loading FlowBoard…</div>
        ) : (
          <Board
            columns={board?.columns ?? []}
            tasks={tasks}
            onCreateTask={(columnId) => setModalState({ open: true, task: null, columnId })}
            onOpenTask={(task) => setModalState({ open: true, task, columnId: task.column_id })}
            onMoveTask={handleMoveTask}
          />
        )}
      </Layout>

      {modalState.open ? (
        <TaskModal
          key={modalState.task?.id ?? modalState.columnId ?? 'new-task'}
          boardId={board?.id}
          columns={board?.columns ?? []}
          task={modalState.task}
          pending={busy}
          onClose={() => setModalState({ open: false, task: null, columnId: null })}
          onSubmit={handleTaskSubmit}
          onDelete={handleTaskDelete}
        />
      ) : null}

      {adminOpen ? (
        <Modal title="Admin" onClose={() => setAdminOpen(false)}>
          <AdminPanel
            columns={board?.columns ?? []}
            rules={rules}
            incomingTasks={incomingTasks}
            pending={busy}
            onCreateColumn={handleCreateColumn}
            onRenameColumn={handleRenameColumn}
            onDeleteColumn={handleDeleteColumn}
            onCreateRule={handleCreateRule}
            onToggleRule={handleToggleRule}
            onDeleteRule={handleDeleteRule}
            onSendDemoTask={handleSendDemoTask}
          />
        </Modal>
      ) : null}

      <Toast toast={toast} />
    </>
  );
}

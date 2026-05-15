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
import NotificationsPanel from './components/NotificationsPanel/NotificationsPanel';
import TaskModal from './components/TaskModal/TaskModal';
import Toast from './components/Ui/Toast';
import { createRealtimeSocket } from './realtime/socket';

function sortColumns(columns) {
  return [...columns].sort((left, right) => left.position - right.position);
}

function sortTasks(tasks) {
  return [...tasks].sort((left, right) => left.position - right.position);
}

export default function App() {
  const [board, setBoard] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [rules, setRules] = useState([]);
  const [incomingTasks, setIncomingTasks] = useState([]);
  const [mode, setMode] = useState('user');
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [modalState, setModalState] = useState({
    open: false,
    task: null,
    columnId: null,
  });
  const [toast, setToast] = useState(null);
  const toastTimeoutRef = useRef(null);

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

  const handleMoveTask = async (task, targetColumnId, position) => {
    await runAction(async () => {
      await moveTask(task.id, {
        column_id: targetColumnId,
        position,
        version: task.version,
      });
      await loadBoard();
    });
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

  const sidePanel =
    mode === 'admin' ? (
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
    ) : (
      <NotificationsPanel
        notifications={notifications}
        pending={busy}
        onMarkRead={handleMarkNotificationRead}
        onMarkAllRead={handleMarkAllNotificationsRead}
      />
    );

  return (
    <>
      <Layout
        connectionStatus={connectionStatus}
        mode={mode}
        onModeChange={setMode}
        onCreateTask={() => setModalState({ open: true, task: null, columnId: board?.columns?.[0]?.id ?? null })}
        boardName={board?.name}
        sidePanel={sidePanel}
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

      <Toast toast={toast} />
    </>
  );
}

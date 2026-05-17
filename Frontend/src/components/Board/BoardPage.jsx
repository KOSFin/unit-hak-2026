import { useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { getBoard, updateBoard } from '../../api/boardsApi';
import { createColumn, deleteColumn, updateColumn } from '../../api/columnsApi';
import { createIncomingTask, getIncomingTasks } from '../../api/incomingTasksApi';
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../../api/notificationsApi';
import { createRule, deleteRule, getRules, updateRule } from '../../api/rulesApi';
import { createTask, deleteTask, getTasks, moveTask, updateTask } from '../../api/tasksApi';
import { uploadImage } from '../../api/uploadsApi';
import { createRealtimeSocket } from '../../realtime/socket';
import { createCrossTabSync } from '../../utils/crossTabSync';
import { getGuestIdentity } from '../../utils/guest';
import AdminPanel from '../AdminPanel/AdminPanel';
import EventFlow from '../EventFlow/EventFlow';
import Layout from '../Layout/Layout';
import TaskModal from '../TaskModal/TaskModal';
import Modal from '../Ui/Modal';
import Board from './Board';
import styles from './BoardPage.module.css';

const PRIORITY_WEIGHT = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};

const DEFAULT_TASK_VIEW = {
  searchQuery: '',
  columnFilter: 'ALL',
  priorityFilter: 'ALL',
  sortMode: 'BOARD_ORDER',
};

function buildPresenceMaps(snapshot, currentGuestId) {
  const editingUsersMap = {};
  const draggingUsersMap = {};

  (snapshot.editing || []).forEach((user) => {
    if (!user.active_task_id || user.guest_id === currentGuestId) {
      return;
    }
    if (!editingUsersMap[user.active_task_id]) {
      editingUsersMap[user.active_task_id] = [];
    }
    editingUsersMap[user.active_task_id].push(user);
  });

  (snapshot.dragging || []).forEach((user) => {
    if (!user.active_task_id || user.guest_id === currentGuestId) {
      return;
    }
    if (!draggingUsersMap[user.active_task_id]) {
      draggingUsersMap[user.active_task_id] = [];
    }
    draggingUsersMap[user.active_task_id].push(user);
  });

  return { editingUsersMap, draggingUsersMap };
}

function generateCorrelationId() {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `corr-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function buildActorSnapshot(identity) {
  return {
    guest_id: identity.id,
    display_name: identity.displayName,
    color: identity.color,
    avatar_url: identity.avatarUrl,
  };
}

export default function BoardPage() {
  const { publicBoardId } = useParams();
  const navigate = useNavigate();

  const [board, setBoard] = useState(null);
  const [columns, setColumns] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [rules, setRules] = useState([]);
  const [incomingTasks, setIncomingTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [taskPending, setTaskPending] = useState(false);
  const [adminPending, setAdminPending] = useState(false);
  const [activeModal, setActiveModal] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [eventFlowOpen, setEventFlowOpen] = useState(false);
  const [identity, setIdentity] = useState(getGuestIdentity());
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [editingUsersMap, setEditingUsersMap] = useState({});
  const [draggingUsersMap, setDraggingUsersMap] = useState({});
  const [realtimeStatus, setRealtimeStatus] = useState('idle');
  const [taskView, setTaskView] = useState({
    boardId: publicBoardId,
    ...DEFAULT_TASK_VIEW,
  });

  const socketRef = useRef(null);
  const crossTabRef = useRef(null);
  const activeTaskView = taskView.boardId === publicBoardId
    ? taskView
    : { boardId: publicBoardId, ...DEFAULT_TASK_VIEW };
  const deferredSearchQuery = useDeferredValue(activeTaskView.searchQuery);
  const activeColumnFilter =
    activeTaskView.columnFilter !== 'ALL' && !columns.some((column) => column.id === activeTaskView.columnFilter)
      ? 'ALL'
      : activeTaskView.columnFilter;

  const refreshTasks = useCallback(async (boardId) => {
    const data = await getTasks(boardId);
    setTasks(data);
  }, []);

  const refreshRules = useCallback(async (boardId) => {
    const data = await getRules(boardId);
    setRules(data);
  }, []);

  const refreshIncomingTasks = useCallback(async (boardId) => {
    const data = await getIncomingTasks(boardId);
    setIncomingTasks(data);
  }, []);

  const refreshNotifications = useCallback(async (boardId) => {
    const data = await getNotifications(boardId);
    setNotifications(data);
  }, []);

  const refreshBoardShell = useCallback(async (targetPublicBoardId) => {
    const boardData = await getBoard(targetPublicBoardId);
    setBoard(boardData);
    setColumns(boardData.columns || []);
    return boardData;
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const boardData = await getBoard(publicBoardId);
        if (cancelled) {
          return;
        }

        setBoard(boardData);
        setColumns(boardData.columns || []);

        const [tasksData, notificationData, rulesData, incomingData] = await Promise.all([
          getTasks(boardData.id),
          getNotifications(boardData.id),
          getRules(boardData.id),
          getIncomingTasks(boardData.id),
        ]);

        if (cancelled) {
          return;
        }

        setTasks(tasksData);
        setNotifications(notificationData);
        setRules(rulesData);
        setIncomingTasks(incomingData);
      } catch (caughtError) {
        if (cancelled) {
          return;
        }
        setBoard(null);
        setColumns([]);
        setTasks([]);
        setRules([]);
        setIncomingTasks([]);
        setNotifications([]);
        setError(caughtError.response?.data?.detail || 'Board not found');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [publicBoardId]);

  useEffect(() => {
    if (!board) {
      return undefined;
    }

    const sendPresenceJoin = (wsClient) => {
      wsClient.send(
        JSON.stringify({
          type: 'presence.join',
          board_id: board.id,
          user: {
            guest_id: identity.id,
            display_name: identity.displayName,
            color: identity.color,
            avatar_url: identity.avatarUrl,
          },
        }),
      );
    };

    const socket = createRealtimeSocket({
      onConnecting: () => {
        setRealtimeStatus('connecting');
      },
      onOpen: (wsClient) => {
        setRealtimeStatus('connected');
        sendPresenceJoin(wsClient);
      },
      onClose: () => {
        setRealtimeStatus('disconnected');
      },
      onError: () => {
        setRealtimeStatus('error');
      },
      onMessage: (message) => {
        if (message.type === 'presence.snapshot' || message.type === 'presence.updated') {
          const snapshot = message.payload || {};
          setOnlineUsers(snapshot.users || []);
          const { editingUsersMap: nextEditing, draggingUsersMap: nextDragging } =
            buildPresenceMaps(snapshot, identity.id);
          setEditingUsersMap(nextEditing);
          setDraggingUsersMap(nextDragging);
          return;
        }

        if (message.type === 'system.error') {
          setRealtimeStatus('error');
          return;
        }

        if (
          message.type === 'task.created' ||
          message.type === 'task.updated' ||
          message.type === 'task.moved' ||
          message.type === 'task.deleted'
        ) {
          refreshTasks(board.id);
          window.dispatchEvent(new Event('board-event-flow-update'));
          return;
        }

        if (
          message.type === 'column.created' ||
          message.type === 'column.updated' ||
          message.type === 'column.deleted'
        ) {
          refreshBoardShell(board.public_id).catch(() => null);
          return;
        }

        if (
          message.type === 'automation-rule.created' ||
          message.type === 'automation-rule.updated' ||
          message.type === 'automation-rule.deleted'
        ) {
          refreshRules(board.id);
          return;
        }

        if (message.type === 'incoming-task.processed') {
          Promise.all([refreshIncomingTasks(board.id), refreshTasks(board.id), refreshNotifications(board.id)])
            .catch(() => null);
          return;
        }

        if (message.type === 'notification.created') {
          refreshNotifications(board.id);
          window.dispatchEvent(new Event('board-event-flow-update'));
        }
      },
    });

    socketRef.current = socket;

    return () => {
      socket.close();
      socketRef.current = null;
      setRealtimeStatus('idle');
      setOnlineUsers([]);
      setEditingUsersMap({});
      setDraggingUsersMap({});
    };
  }, [
    board,
    identity,
    refreshBoardShell,
    refreshIncomingTasks,
    refreshNotifications,
    refreshRules,
    refreshTasks,
  ]);
  // Cross-tab synchronization setup
  useEffect(() => {
    if (!publicBoardId) {
      return undefined;
    }

    const crossTab = createCrossTabSync(publicBoardId);
    crossTabRef.current = crossTab;

    // Listen for task updates from other tabs
    const unsubscribeTasks = crossTab.on('tasks-updated', (payload) => {
      if (payload && Array.isArray(payload)) {
        setTasks(payload);
      }
    });

    // Listen for board state updates from other tabs
    const unsubscribeBoard = crossTab.on('board-updated', (payload) => {
      if (payload) {
        setBoard(payload);
        setColumns(payload.columns || []);
      }
    });

    // Listen for notifications from other tabs
    const unsubscribeNotifications = crossTab.on('notifications-updated', (payload) => {
      if (payload && Array.isArray(payload)) {
        setNotifications(payload);
      }
    });

    // Listen for rules updates from other tabs
    const unsubscribeRules = crossTab.on('rules-updated', (payload) => {
      if (payload && Array.isArray(payload)) {
        setRules(payload);
      }
    });

    // Listen for incoming tasks updates from other tabs
    const unsubscribeIncoming = crossTab.on('incoming-tasks-updated', (payload) => {
      if (payload && Array.isArray(payload)) {
        setIncomingTasks(payload);
      }
    });

    return () => {
      unsubscribeTasks();
      unsubscribeBoard();
      unsubscribeNotifications();
      unsubscribeRules();
      unsubscribeIncoming();
      crossTab.dispose();
      crossTabRef.current = null;
    };
  }, [publicBoardId]);

  // Broadcast state changes to other tabs
  useEffect(() => {
    if (!crossTabRef.current) {
      return;
    }
    crossTabRef.current.send('tasks-updated', tasks);
  }, [tasks]);

  useEffect(() => {
    if (!crossTabRef.current) {
      return;
    }
    crossTabRef.current.send('board-updated', board);
  }, [board]);

  useEffect(() => {
    if (!crossTabRef.current) {
      return;
    }
    crossTabRef.current.send('notifications-updated', notifications);
  }, [notifications]);

  useEffect(() => {
    if (!crossTabRef.current) {
      return;
    }
    crossTabRef.current.send('rules-updated', rules);
  }, [rules]);

  useEffect(() => {
    if (!crossTabRef.current) {
      return;
    }
    crossTabRef.current.send('incoming-tasks-updated', incomingTasks);
  }, [incomingTasks]);
  const sendWsUpdate = useCallback(
    (type, extra = {}) => {
      if (!board || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        return;
      }

      socketRef.current.send(
        JSON.stringify({
          type,
          board_id: board.id,
          user: {
            guest_id: identity.id,
            display_name: identity.displayName,
            color: identity.color,
            avatar_url: identity.avatarUrl,
            ...extra,
          },
        }),
      );
    },
    [board, identity],
  );

  useEffect(() => {
    const onEditStart = (event) => sendWsUpdate('editing.started', { active_task_id: event.detail });
    const onEditEnd = () => sendWsUpdate('editing.ended');

    window.addEventListener('task-edit-start', onEditStart);
    window.addEventListener('task-edit-end', onEditEnd);
    return () => {
      window.removeEventListener('task-edit-start', onEditStart);
      window.removeEventListener('task-edit-end', onEditEnd);
    };
  }, [sendWsUpdate]);

  const handleOpenTaskModal = useCallback((task = null) => {
    setActiveTask(task);
    setActiveModal('task');
  }, []);

  const handleCloseTaskModal = useCallback(() => {
    setActiveModal((current) => (current === 'task' ? null : current));
    setActiveTask(null);
  }, []);

  const handleSaveTask = useCallback(
    async (payload) => {
      if (!board) {
        return;
      }

      setTaskPending(true);
      try {
        const correlationId = generateCorrelationId();
        const payloadWithContext = {
          ...payload,
          board_id: board.id,
          guest_id: identity.id,
          correlation_id: correlationId,
          actor: buildActorSnapshot(identity),
        };

        if (activeTask?.id) {
          const updated = await updateTask(activeTask.id, {
            ...payloadWithContext,
            version: activeTask.version,
          });
          setTasks((current) => current.map((task) => (task.id === updated.id ? updated : task)));
        } else {
          const created = await createTask(payloadWithContext);
          setTasks((current) => [...current, created]);
        }

        handleCloseTaskModal();
        window.dispatchEvent(new Event('board-event-flow-update'));
      } catch (caughtError) {
        alert(caughtError.response?.data?.detail || 'Failed to save task');
      } finally {
        setTaskPending(false);
      }
    },
    [activeTask, board, handleCloseTaskModal, identity],
  );

  const handleDeleteTask = useCallback(
    async (task) => {
      if (!board || !window.confirm('Delete task?')) {
        return;
      }

      setTaskPending(true);
      try {
        await deleteTask(task.id, board.id);
        setTasks((current) => current.filter((item) => item.id !== task.id));
        handleCloseTaskModal();
        window.dispatchEvent(new Event('board-event-flow-update'));
      } catch (caughtError) {
        alert(caughtError.response?.data?.detail || 'Failed to delete task');
      } finally {
        setTaskPending(false);
      }
    },
    [board, handleCloseTaskModal],
  );

  const handleMoveTask = useCallback(
    async (task, targetColumnId, targetIndex) => {
      if (!board) {
        return;
      }

      try {
        const moved = await moveTask(
          task.id,
          {
            column_id: targetColumnId,
            position: targetIndex + 1,
            version: task.version,
            guest_id: identity.id,
            correlation_id: generateCorrelationId(),
            actor: buildActorSnapshot(identity),
          },
          board.id,
        );
        setTasks((current) => current.map((item) => (item.id === moved.id ? moved : item)));
        window.dispatchEvent(new Event('board-event-flow-update'));
      } catch {
        refreshTasks(board.id).catch(() => null);
      }
    },
    [board, identity, refreshTasks],
  );

  const handleCreateColumn = useCallback(
    async (title) => {
      if (!board) {
        return;
      }

      setAdminPending(true);
      try {
        const created = await createColumn({ board_id: board.id, title });
        setColumns((current) => [...current, created]);
        window.dispatchEvent(new Event('board-event-flow-update'));
      } finally {
        setAdminPending(false);
      }
    },
    [board],
  );

  const handleRenameColumn = useCallback(async (columnId, title) => {
    if (!title.trim()) {
      return;
    }

    setAdminPending(true);
    try {
      const updated = await updateColumn(columnId, { title: title.trim() });
      setColumns((current) => current.map((column) => (column.id === updated.id ? updated : column)));
      window.dispatchEvent(new Event('board-event-flow-update'));
    } finally {
      setAdminPending(false);
    }
  }, []);

  const handleDeleteColumn = useCallback(
    async (columnId) => {
      if (!board) {
        return;
      }

      setAdminPending(true);
      try {
        await deleteColumn(columnId, board.id);
        setColumns((current) => current.filter((column) => column.id !== columnId));
        window.dispatchEvent(new Event('board-event-flow-update'));
      } catch (caughtError) {
        alert(caughtError.response?.data?.detail || 'Failed to delete column');
      } finally {
        setAdminPending(false);
      }
    },
    [board],
  );

  const handleCreateRule = useCallback(
    async (payload) => {
      if (!board) {
        return;
      }

      setAdminPending(true);
      try {
        const created = await createRule({ ...payload, board_id: board.id });
        setRules((current) => [...current, created]);
        window.dispatchEvent(new Event('board-event-flow-update'));
      } finally {
        setAdminPending(false);
      }
    },
    [board],
  );

  const handleToggleRule = useCallback(async (rule) => {
    setAdminPending(true);
    try {
      const updated = await updateRule(rule.id, { enabled: !rule.enabled });
      setRules((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      window.dispatchEvent(new Event('board-event-flow-update'));
    } finally {
      setAdminPending(false);
    }
  }, []);

  const handleDeleteRule = useCallback(async (ruleId) => {
    setAdminPending(true);
    try {
      await deleteRule(ruleId);
      setRules((current) => current.filter((rule) => rule.id !== ruleId));
      window.dispatchEvent(new Event('board-event-flow-update'));
    } finally {
      setAdminPending(false);
    }
  }, []);

  const handleSendDemoTask = useCallback(
    async () => {
      if (!board) {
        return;
      }

      setAdminPending(true);
      try {
        const created = await createIncomingTask({
          board_id: board.id,
          external_id: `demo-${Date.now()}`,
          raw_payload: {
            title: 'Urgent queue task',
            description: 'Created from the Event Flow demo panel.',
            tags: ['urgent', 'queue'],
          },
        });
        setIncomingTasks((current) => [created, ...current]);
        window.dispatchEvent(new Event('board-event-flow-update'));
      } finally {
        setAdminPending(false);
      }
    },
    [board],
  );

  const handleBoardImageUpdate = useCallback(
    async (file, input) => {
      if (!board || !file) {
        if (input) {
          input.value = '';
        }
        return;
      }

      setAdminPending(true);
      try {
        const uploaded = await uploadImage(file);
        const updatedBoard = await updateBoard(board.public_id, {
          image_path: uploaded.path,
        });
        setBoard(updatedBoard);
        setColumns(updatedBoard.columns || []);
      } catch (caughtError) {
        alert(caughtError.response?.data?.detail || 'Failed to update board image');
      } finally {
        if (input) {
          input.value = '';
        }
        setAdminPending(false);
      }
    },
    [board],
  );

  const filteredTasks = useMemo(() => {
    const searchNeedle = deferredSearchQuery.trim().toLowerCase();
    const columnTitles = new Map(columns.map((column) => [column.id, column.title]));

    const nextTasks = tasks.filter((task) => {
      if (activeColumnFilter !== 'ALL' && task.column_id !== activeColumnFilter) {
        return false;
      }

      if (activeTaskView.priorityFilter !== 'ALL' && task.priority !== activeTaskView.priorityFilter) {
        return false;
      }

      if (!searchNeedle) {
        return true;
      }

      const searchTarget = [
        task.title,
        task.description,
        task.status,
        columnTitles.get(task.column_id),
        task.id.slice(0, 8),
        ...(task.tags ?? []),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      return searchTarget.includes(searchNeedle);
    });

    if (activeTaskView.sortMode === 'BOARD_ORDER') {
      return nextTasks;
    }

    return [...nextTasks].sort((left, right) => {
      if (activeTaskView.sortMode === 'UPDATED_DESC') {
        return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
      }

      if (activeTaskView.sortMode === 'PRIORITY_DESC') {
        const priorityDiff = PRIORITY_WEIGHT[left.priority] - PRIORITY_WEIGHT[right.priority];
        if (priorityDiff !== 0) {
          return priorityDiff;
        }
        return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
      }

      if (activeTaskView.sortMode === 'DEADLINE_ASC') {
        const leftDeadline = left.deadline ? new Date(left.deadline).getTime() : Number.POSITIVE_INFINITY;
        const rightDeadline = right.deadline ? new Date(right.deadline).getTime() : Number.POSITIVE_INFINITY;
        if (leftDeadline !== rightDeadline) {
          return leftDeadline - rightDeadline;
        }
        return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
      }

      if (activeTaskView.sortMode === 'TITLE_ASC') {
        return left.title.localeCompare(right.title, undefined, { sensitivity: 'base' });
      }

      return 0;
    });
  }, [activeColumnFilter, activeTaskView.priorityFilter, activeTaskView.sortMode, columns, deferredSearchQuery, tasks]);

  const taskViewActive =
    activeTaskView.searchQuery.trim().length > 0 ||
    activeColumnFilter !== 'ALL' ||
    activeTaskView.priorityFilter !== 'ALL' ||
    activeTaskView.sortMode !== 'BOARD_ORDER';

  if (loading) {
    return (
      <div className={styles.statePage}>
        <div className={styles.stateCard}>
          <p className={styles.stateEyebrow}>FlowBoard</p>
          <h1>Loading board…</h1>
          <p>We’re pulling the latest tasks, activity, and presence for this workspace.</p>
        </div>
      </div>
    );
  }

  if (error || !board) {
    return (
      <div className={styles.statePage}>
        <div className={styles.stateCard}>
          <p className={styles.stateEyebrow}>Board unavailable</p>
          <h1>Board not found or already removed</h1>
          <p>
            This temporary board may have expired after inactivity, or the link may be incomplete.
          </p>
          <div className={styles.stateActions}>
            <button type="button" className={styles.secondaryButton} onClick={() => navigate('/')}>
              Create a new board
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Layout
      board={board}
      identity={identity}
      columns={columns}
      onlineUsers={onlineUsers}
      realtimeStatus={realtimeStatus}
      onUpdateIdentity={(updated) => {
        setIdentity(updated);
        sendWsUpdate('presence.update', {
          display_name: updated.displayName,
          color: updated.color,
          avatar_url: updated.avatarUrl,
        });
      }}
      onCreateTask={() => handleOpenTaskModal()}
      onOpenAdmin={() => setActiveModal('admin')}
      onToggleEventFlow={() => setEventFlowOpen((current) => !current)}
      notifications={notifications}
      notificationsOpen={notificationsOpen}
      pending={taskPending || adminPending}
      onUpdateBoardImage={handleBoardImageUpdate}
      onToggleNotifications={() => setNotificationsOpen((current) => !current)}
      onCloseNotifications={() => setNotificationsOpen(false)}
      mainClassName={styles.layoutMain}
      searchQuery={activeTaskView.searchQuery}
      onSearchQueryChange={(value) =>
        setTaskView((current) => ({
          ...(current.boardId === publicBoardId ? current : { boardId: publicBoardId, ...DEFAULT_TASK_VIEW }),
          boardId: publicBoardId,
          searchQuery: value,
        }))
      }
      columnFilter={activeColumnFilter}
      onColumnFilterChange={(value) =>
        setTaskView((current) => ({
          ...(current.boardId === publicBoardId ? current : { boardId: publicBoardId, ...DEFAULT_TASK_VIEW }),
          boardId: publicBoardId,
          columnFilter: value,
        }))
      }
      priorityFilter={activeTaskView.priorityFilter}
      onPriorityFilterChange={(value) =>
        setTaskView((current) => ({
          ...(current.boardId === publicBoardId ? current : { boardId: publicBoardId, ...DEFAULT_TASK_VIEW }),
          boardId: publicBoardId,
          priorityFilter: value,
        }))
      }
      sortMode={activeTaskView.sortMode}
      onSortModeChange={(value) =>
        setTaskView((current) => ({
          ...(current.boardId === publicBoardId ? current : { boardId: publicBoardId, ...DEFAULT_TASK_VIEW }),
          boardId: publicBoardId,
          sortMode: value,
        }))
      }
      onResetTaskView={() => {
        setTaskView({
          boardId: publicBoardId,
          ...DEFAULT_TASK_VIEW,
        });
      }}
      visibleTaskCount={filteredTasks.length}
      totalTaskCount={tasks.length}
      taskViewActive={taskViewActive}
      onMarkNotificationRead={async (notificationId) => {
        if (!board) {
          return;
        }
        const updated = await markNotificationRead(notificationId, board.id);
        setNotifications((current) =>
          current.map((notification) =>
            notification.id === updated.id ? updated : notification,
          ),
        );
      }}
      onMarkAllNotificationsRead={async () => {
        if (!board) {
          return;
        }
        await markAllNotificationsRead(board.id);
        setNotifications((current) => current.map((notification) => ({ ...notification, read: true })));
      }}
    >
      <div
        className={`${styles.boardLayout} ${eventFlowOpen ? styles.boardLayoutWithAside : ''}`.trim()}
      >
        <div className={styles.boardShell}>
          <Board
            columns={columns}
            tasks={filteredTasks}
            onCreateTask={(columnId) => handleOpenTaskModal({ column_id: columnId })}
            onOpenTask={handleOpenTaskModal}
            onMoveTask={handleMoveTask}
            editingUsersMap={editingUsersMap}
            draggingUsersMap={draggingUsersMap}
            onDragStartEmit={(taskId) => sendWsUpdate('drag.started', { active_task_id: taskId })}
            onDragEndEmit={() => sendWsUpdate('drag.ended')}
            dragDisabled={taskViewActive}
          />
        </div>

        {eventFlowOpen ? <EventFlow boardId={board.public_id} onlineUsers={onlineUsers} /> : null}
      </div>

      {activeModal === 'task' ? (
        <TaskModal
          boardId={board.id}
          columns={columns}
          task={activeTask}
          pending={taskPending}
          onClose={handleCloseTaskModal}
          onSubmit={handleSaveTask}
          onDelete={handleDeleteTask}
        />
      ) : null}

      {activeModal === 'admin' ? (
        <Modal title="Admin Panel" onClose={() => setActiveModal(null)}>
          <AdminPanel
            columns={columns}
            rules={rules}
            incomingTasks={incomingTasks}
            pending={adminPending}
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
    </Layout>
  );
}

import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBoard } from '../../api/boardsApi';
import Layout from '../Layout/Layout';
import Board from './Board';
import AdminPanel from '../AdminPanel/AdminPanel';
import NotificationsPanel from '../NotificationsPanel/NotificationsPanel';
import RulesPanel from '../RulesPanel/RulesPanel';
import IncomingTasksPanel from '../IncomingTasksPanel/IncomingTasksPanel';
import TaskModal from '../TaskModal/TaskModal';
import EventFlow from '../EventFlow/EventFlow';
import { getColumns, createColumn, updateColumn, deleteColumn } from '../../api/columnsApi';
import { getTasks, createTask, updateTask, moveTask, deleteTask } from '../../api/tasksApi';
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../../api/notificationsApi';
import { getGuestIdentity } from '../../utils/guest';
import { createRealtimeSocket } from '../../realtime/socket';

export default function BoardPage() {
  const { publicBoardId } = useParams();
  const navigate = useNavigate();

  const [board, setBoard] = useState(null);
  const [columns, setColumns] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeModal, setActiveModal] = useState(null);
  const [activeTask, setActiveTask] = useState(null);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [eventFlowOpen, setEventFlowOpen] = useState(false);

  const [identity, setIdentity] = useState(getGuestIdentity());
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [editingUsersMap, setEditingUsersMap] = useState({});
  const [draggingUsersMap, setDraggingUsersMap] = useState({});
  
  const socketRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const boardData = await getBoard(publicBoardId);
        setBoard(boardData);
        setColumns(boardData.columns || []);

        const [tasksData, notifData] = await Promise.all([
          getTasks(boardData.id),
          getNotifications(boardData.id)
        ]);
        setTasks(tasksData);
        setNotifications(notifData);
      } catch (err) {
        setError(err.response?.data?.detail || "Board not found");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [publicBoardId]);

  useEffect(() => {
    if (!board) return;

    const ws = createRealtimeSocket({
      onOpen: () => {
        ws.send(JSON.stringify({
          type: 'presence.join',
          board_id: board.public_id,
          user: {
            guest_id: identity.id,
            display_name: identity.displayName,
            color: identity.color,
            avatar_url: identity.avatarUrl
          }
        }));
      },
      onMessage: (msg) => {
        if (msg.type === 'presence.snapshot' || msg.type === 'presence.updated') {
          const payload = msg.payload;
          setOnlineUsers(payload.users || []);
          
          const eMap = {};
          (payload.editing || []).forEach(u => {
             if(u.active_task_id && u.guest_id !== identity.id) {
               if(!eMap[u.active_task_id]) eMap[u.active_task_id] = [];
               eMap[u.active_task_id].push(u);
             }
          });
          setEditingUsersMap(eMap);
          
          const dMap = {};
          (payload.dragging || []).forEach(u => {
             if(u.active_task_id && u.guest_id !== identity.id) {
               if(!dMap[u.active_task_id]) dMap[u.active_task_id] = [];
               dMap[u.active_task_id].push(u);
             }
          });
          setDraggingUsersMap(dMap);
        } else {
           // Other realtime events
           if(msg.type === 'task.created' || msg.type === 'task.updated' || msg.type === 'task.moved' || msg.type === 'task.deleted') {
              getTasks(board.id).then(setTasks);
              window.dispatchEvent(new Event('board-event-flow-update'));
           }
        }
      }
    });

    socketRef.current = ws;

    return () => {
      ws.close();
    };
  }, [board, identity]);
  
  const sendWsUpdate = useCallback((type, extra = {}) => {
     if(socketRef.current && socketRef.current.readyState === WebSocket.OPEN && board) {
        socketRef.current.send(JSON.stringify({
           type,
           board_id: board.public_id,
           user: {
              guest_id: identity.id,
              ...extra
           }
        }));
     }
  }, [board, identity]);

  useEffect(() => {
     const onEditStart = (e) => sendWsUpdate('editing.started', { active_task_id: e.detail });
     const onEditEnd = (e) => sendWsUpdate('editing.ended', { active_task_id: e.detail });
     
     window.addEventListener('task-edit-start', onEditStart);
     window.addEventListener('task-edit-end', onEditEnd);
     return () => {
        window.removeEventListener('task-edit-start', onEditStart);
        window.removeEventListener('task-edit-end', onEditEnd);
     };
  }, [sendWsUpdate]);

  const handleOpenTaskModal = (task = null) => {
    setActiveTask(task);
    setActiveModal('task');
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    setActiveTask(null);
  };

  const handleSaveTask = async (payload) => {
    try {
      const payloadWithGuest = { ...payload, guest_id: identity.id, board_id: board.id };
      if (activeTask) {
        const updated = await updateTask(activeTask.id, {
          ...payloadWithGuest,
          version: activeTask.version,
        });
        setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
      } else {
        const created = await createTask(payloadWithGuest);
        setTasks((prev) => [...prev, created]);
      }
      handleCloseModal();
      window.dispatchEvent(new Event('board-event-flow-update'));
    } catch (err) {
      alert("Failed to save task");
    }
  };

  const handleDeleteTask = async (task) => {
    if (!window.confirm("Delete task?")) return;
    try {
      await deleteTask(task.id, board.id);
      setTasks((prev) => prev.filter((t) => t.id !== task.id));
      handleCloseModal();
      window.dispatchEvent(new Event('board-event-flow-update'));
    } catch (err) {
      alert("Failed to delete task");
    }
  };

  const handleMoveTask = useCallback(async (task, targetColumnId, targetIndex) => {
    const position = targetIndex + 1;
    try {
      const moved = await moveTask(task.id, {
        column_id: targetColumnId,
        position,
        version: task.version,
        guest_id: identity.id
      }, board.id);
      setTasks((prev) => prev.map((t) => (t.id === moved.id ? moved : t)));
      window.dispatchEvent(new Event('board-event-flow-update'));
    } catch (err) {
      console.error(err);
      getTasks(board.id).then(setTasks);
    }
  }, [board, identity]);

  if (loading) return <div>Loading...</div>;
  if (error || !board) return <div>{error || "Error loading board"}</div>;

  return (
    <Layout
      board={board}
      identity={identity}
      onlineUsers={onlineUsers}
      onUpdateIdentity={(updated) => {
         setIdentity(updated);
         sendWsUpdate('presence.update', { display_name: updated.displayName, color: updated.color, avatar_url: updated.avatarUrl });
      }}
      onCreateTask={() => handleOpenTaskModal()}
      onOpenAdmin={() => setActiveModal('admin')}
      onToggleEventFlow={() => setEventFlowOpen(!eventFlowOpen)}
      notifications={notifications}
      notificationsOpen={notificationsOpen}
      onToggleNotifications={() => setNotificationsOpen(!notificationsOpen)}
      onCloseNotifications={() => setNotificationsOpen(false)}
      onMarkNotificationRead={async (id) => {
        await markNotificationRead(id, board.id);
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      }}
      onMarkAllNotificationsRead={async () => {
        await markAllNotificationsRead(board.id);
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      }}
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <Board
            columns={columns}
            tasks={tasks}
            onCreateTask={(colId) => handleOpenTaskModal({ column_id: colId })}
            onOpenTask={handleOpenTaskModal}
            onMoveTask={handleMoveTask}
            editingUsersMap={editingUsersMap}
            draggingUsersMap={draggingUsersMap}
            onDragStartEmit={(taskId) => sendWsUpdate('drag.started', { active_task_id: taskId })}
            onDragEndEmit={() => sendWsUpdate('drag.ended')}
          />
        </div>
        {eventFlowOpen && <EventFlow boardId={board.public_id} onlineUsers={onlineUsers} />}
      </div>

      {activeModal === 'task' && (
        <TaskModal
          boardId={board.id}
          columns={columns}
          task={activeTask}
          onClose={handleCloseModal}
          onSubmit={handleSaveTask}
          onDelete={handleDeleteTask}
        />
      )}

      {activeModal === 'admin' && (
        <AdminPanel
          onClose={handleCloseModal}
          onOpenRules={() => setActiveModal('rules')}
          onOpenNotifications={() => setActiveModal('notifications')}
          onOpenIncoming={() => setActiveModal('incoming')}
        />
      )}

      {activeModal === 'rules' && (
         <RulesPanel onClose={() => setActiveModal('admin')} boardId={board.id} />
      )}

      {activeModal === 'notifications' && (
         <NotificationsPanel onClose={() => setActiveModal('admin')} boardId={board.id} />
      )}

      {activeModal === 'incoming' && (
         <IncomingTasksPanel onClose={() => setActiveModal('admin')} boardId={board.id} />
      )}
    </Layout>
  );
}

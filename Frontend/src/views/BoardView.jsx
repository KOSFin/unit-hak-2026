import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import Modal, { modalCss as m } from '../components/Modal.jsx';
import Topbar from '../components/Topbar.jsx';
import { useWsEvent } from '../contexts/WsContext.jsx';
import s from './BoardView.module.css';

// ── Task Card ────────────────────────────────────────────────────────────────
function TaskCard({ task, onDragStart, onClick }) {
  return (
    <article
      id={`task-${task.id}`}
      className={s.card}
      draggable
      onDragStart={() => onDragStart(task)}
      onClick={() => onClick(task)}
      aria-label={`Task: ${task.title}`}
    >
      <p className={s.cardTitle}>{task.title}</p>
      <div className={s.cardMeta}>
        {task.priority && (
          <span className={`${s.priority} ${s[task.priority]}`}>{task.priority}</span>
        )}
        {(task.tags ?? []).map((t) => <span key={t} className={s.tag}>{t}</span>)}
        {task.deadline && (
          <span className={s.deadline}>
            📅 {new Date(task.deadline).toLocaleDateString()}
          </span>
        )}
      </div>
    </article>
  );
}

// ── Add/Edit Task Modal ──────────────────────────────────────────────────────
function TaskModal({ boardId, columns, editTask, onClose, onSaved }) {
  const isEdit = Boolean(editTask);
  const [form, setForm] = useState({
    title: editTask?.title ?? '',
    description: editTask?.description ?? '',
    status: editTask?.status ?? '',
    priority: editTask?.priority ?? 'MEDIUM',
    tags: (editTask?.tags ?? []).join(', '),
    deadline: editTask?.deadline ? editTask.deadline.slice(0, 10) : '',
    column_id: editTask?.column_id ?? columns[0]?.id ?? '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async () => {
    if (!form.title.trim()) { setError('Title is required.'); return; }
    setLoading(true);
    setError('');
    try {
      const payload = {
        title: form.title.trim(),
        description: form.description || null,
        status: form.status || form.column_id,
        priority: form.priority,
        tags: form.tags ? form.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
        deadline: form.deadline || null,
        column_id: form.column_id,
      };
      if (isEdit) {
        await api.updateTask(boardId, editTask.id, payload);
      } else {
        await api.createTask(boardId, payload);
      }
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Edit Task' : 'New Task'}
      onClose={onClose}
      footer={
        <>
          <button className={m.btnGhost} onClick={onClose}>Cancel</button>
          <button id="btn-save-task" className={m.btnPrimary} onClick={submit} disabled={loading}>
            {loading ? 'Saving…' : isEdit ? 'Save' : 'Create'}
          </button>
        </>
      }
    >
      {error && <p className={m.error}>{error}</p>}
      <div className={m.field}>
        <label className={m.label} htmlFor="task-title">Title *</label>
        <input id="task-title" className={m.input} value={form.title} onChange={set('title')} autoFocus />
      </div>
      <div className={m.field}>
        <label className={m.label} htmlFor="task-desc">Description</label>
        <textarea id="task-desc" className={m.textarea} value={form.description} onChange={set('description')} />
      </div>
      <div className={m.field}>
        <label className={m.label} htmlFor="task-col">Column</label>
        <select id="task-col" className={m.select} value={form.column_id} onChange={set('column_id')}>
          {columns.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
        </select>
      </div>
      <div className={m.field}>
        <label className={m.label} htmlFor="task-priority">Priority</label>
        <select id="task-priority" className={m.select} value={form.priority} onChange={set('priority')}>
          {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((p) => <option key={p}>{p}</option>)}
        </select>
      </div>
      <div className={m.field}>
        <label className={m.label} htmlFor="task-tags">Tags (comma-separated)</label>
        <input id="task-tags" className={m.input} value={form.tags} onChange={set('tags')} placeholder="e.g. bug, frontend" />
      </div>
      <div className={m.field}>
        <label className={m.label} htmlFor="task-deadline">Deadline</label>
        <input id="task-deadline" className={m.input} type="date" value={form.deadline} onChange={set('deadline')} />
      </div>
    </Modal>
  );
}

// ── Column Modal ─────────────────────────────────────────────────────────────
function ColumnModal({ boardId, onClose, onSaved }) {
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    if (!title.trim()) { setError('Title is required.'); return; }
    setLoading(true);
    try {
      await api.createColumn(boardId, { title: title.trim() });
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="New Column"
      onClose={onClose}
      footer={
        <>
          <button className={m.btnGhost} onClick={onClose}>Cancel</button>
          <button id="btn-save-column" className={m.btnPrimary} onClick={submit} disabled={loading}>
            {loading ? 'Creating…' : 'Create'}
          </button>
        </>
      }
    >
      {error && <p className={m.error}>{error}</p>}
      <div className={m.field}>
        <label className={m.label} htmlFor="col-title">Column Title *</label>
        <input id="col-title" className={m.input} value={title} onChange={(e) => setTitle(e.target.value)} autoFocus />
      </div>
    </Modal>
  );
}

// ── Board View ────────────────────────────────────────────────────────────────
export default function BoardView({ boardId, wsConnected }) {
  const [columns, setColumns] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // 'task' | 'column' | 'editTask'
  const [editTask, setEditTask] = useState(null);
  const [activeColForTask, setActiveColForTask] = useState(null);
  const dragTask = useRef(null);
  const [dragOverCol, setDragOverCol] = useState(null);
  const wsEvent = useWsEvent();

  const load = useCallback(async () => {
    if (!boardId) return;
    try {
      const [cols, tks] = await Promise.all([api.getColumns(boardId), api.getTasks(boardId)]);
      setColumns(cols.sort((a, b) => a.position - b.position));
      setTasks(tks);
    } catch (e) {
      console.error('Failed to load board data', e);
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  useEffect(() => { load(); }, [load]);

  // Refresh on WS event
  useEffect(() => {
    if (wsEvent) load();
  }, [wsEvent, load]);

  // Drag-and-drop
  const onDragStart = (task) => { dragTask.current = task; };
  const onDragOver = (e, colId) => { e.preventDefault(); setDragOverCol(colId); };
  const onDrop = async (colId) => {
    setDragOverCol(null);
    const task = dragTask.current;
    if (!task || task.column_id === colId) return;
    // Optimistic UI
    setTasks((prev) => prev.map((t) => t.id === task.id ? { ...t, column_id: colId } : t));
    try {
      await api.moveTask(boardId, task.id, { column_id: colId, position: 1 });
    } catch {
      load(); // rollback
    }
  };

  const openAddTask = (colId) => {
    setActiveColForTask(colId);
    setEditTask(null);
    setModal('task');
  };

  const openEditTask = (task) => {
    setEditTask(task);
    setModal('editTask');
  };

  const deleteTask = async (taskId) => {
    if (!confirm('Delete this task?')) return;
    await api.deleteTask(boardId, taskId);
    load();
  };

  if (!boardId) return (
    <div style={{ padding: '48px', color: 'var(--color-text-muted)', textAlign: 'center' }}>
      <p>No board found. Create a board to get started.</p>
    </div>
  );

  return (
    <>
      <Topbar
        title="Kanban Board"
        wsConnected={wsConnected}
        onAdd={() => setModal('column')}
        addLabel="Add Column"
      />

      <main style={{ paddingTop: 'var(--topbar-height)' }}>
        {loading ? (
          <div style={{ padding: '48px', color: 'var(--color-text-muted)', textAlign: 'center' }}>Loading…</div>
        ) : (
          <div className={s.board} aria-label="Kanban board">
            {columns.map((col) => {
              const colTasks = tasks.filter((t) => t.column_id === col.id);
              return (
                <div
                  key={col.id}
                  id={`col-${col.id}`}
                  className={`${s.column}${dragOverCol === col.id ? ' ' + s.dragOver : ''}`}
                  onDragOver={(e) => onDragOver(e, col.id)}
                  onDrop={() => onDrop(col.id)}
                  onDragLeave={() => setDragOverCol(null)}
                  aria-label={`Column: ${col.title}`}
                >
                  <div className={s.colHeader}>
                    <span className={s.colTitle}>{col.title}</span>
                    <span className={s.colCount}>{colTasks.length}</span>
                  </div>
                  <div className={s.taskList}>
                    {colTasks.length === 0 && (
                      <p className={s.emptyState}>Drop tasks here</p>
                    )}
                    {colTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onDragStart={onDragStart}
                        onClick={openEditTask}
                      />
                    ))}
                  </div>
                  <button
                    id={`btn-add-task-${col.id}`}
                    className={s.addTaskBtn}
                    onClick={() => openAddTask(col.id)}
                  >
                    + Add Task
                  </button>
                </div>
              );
            })}

            <button
              id="btn-add-column"
              className={s.addColBtn}
              onClick={() => setModal('column')}
            >
              + Add Column
            </button>
          </div>
        )}
      </main>

      {(modal === 'task' || modal === 'editTask') && (
        <TaskModal
          boardId={boardId}
          columns={columns}
          editTask={modal === 'editTask' ? editTask : null}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); }}
        />
      )}

      {modal === 'column' && (
        <ColumnModal
          boardId={boardId}
          onClose={() => setModal(null)}
          onSaved={() => { setModal(null); load(); }}
        />
      )}
    </>
  );
}

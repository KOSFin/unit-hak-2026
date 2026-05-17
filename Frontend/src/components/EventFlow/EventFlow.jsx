import { useEffect, useState, useRef } from 'react';
import Badge from '../Ui/Badge';
import { getBoardEvents } from '../../api/boardsApi';
import styles from './EventFlow.module.css';

const SOURCE_COLORS = {
  USER: 'accent',
  API: 'neutral',
  DB: 'warning',
  QUEUE: 'danger',
  WORKER: 'danger',
  RULE: 'warning',
  WS: 'neutral',
  SYSTEM: 'neutral',
};

function describeEvent(event) {
  const task = event.payload?.task;
  const notification = event.payload?.notification;
  const incomingTask = event.payload?.incoming_task;
  const rule = event.payload?.rule;
  const message = event.payload?.message;

  if (event.type === 'TASK_CREATED') {
    return {
      title: 'Task created',
      message: task?.title ? `"${task.title}" entered the board.` : 'A new task entered the board.',
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'TASK_UPDATED') {
    return {
      title: 'Task updated',
      message: task?.title ? `"${task.title}" was edited.` : 'A task was edited.',
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'TASK_MOVED') {
    return {
      title: 'Task moved',
      message: task?.title
        ? `"${task.title}" moved to ${task.status || 'a new column'}.`
        : 'A task changed column.',
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'TASK_DELETED') {
    return {
      title: 'Task removed',
      message: task?.title ? `"${task.title}" left the board.` : 'A task was removed.',
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'NOTIFICATION_CREATED') {
    return {
      title: 'Notification delivered',
      message: notification?.message || notification?.title || 'A new notification was generated.',
    };
  }

  if (event.type === 'INCOMING_TASK_RECEIVED') {
    return {
      title: 'Incoming task received',
      message: incomingTask?.external_id
        ? `Payload ${incomingTask.external_id} entered the queue.`
        : 'A payload entered the queue.',
    };
  }

  if (event.type === 'INCOMING_TASK_VALIDATED') {
    return {
      title: 'Incoming task validated',
      message: 'The payload passed validation and is ready for worker processing.',
    };
  }

  if (event.type === 'INCOMING_TASK_PROCESSED') {
    return {
      title: 'Incoming task processed',
      message: task?.title
        ? `Worker turned the payload into "${task.title}".`
        : 'Worker created a task from the payload.',
    };
  }

  if (event.type === 'AUTOMATION_TRIGGERED') {
    return {
      title: 'Automation triggered',
      message: message || 'A rule reacted to the latest board event.',
    };
  }

  if (event.type === 'AUTOMATION_RULE_CREATED') {
    return {
      title: 'Rule created',
      message: rule?.name ? `"${rule.name}" is now active for this board.` : 'A rule was created.',
    };
  }

  if (event.type === 'AUTOMATION_RULE_UPDATED') {
    return {
      title: 'Rule updated',
      message: rule?.name ? `"${rule.name}" changed its behavior.` : 'A rule was updated.',
    };
  }

  if (event.type === 'AUTOMATION_RULE_DELETED') {
    return {
      title: 'Rule deleted',
      message: rule?.name ? `"${rule.name}" was removed.` : 'A rule was deleted.',
    };
  }

  return {
    title: event.type.replaceAll('_', ' '),
    message: message || 'System activity recorded for this board.',
    guestId: task?.guest_id,
  };
}

export default function EventFlow({ boardId, onlineUsers = [] }) {
  const [groups, setGroups] = useState([]);
  const containerRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getBoardEvents(boardId);
        setGroups(data);
      } catch (err) {
        console.error("Failed to load events", err);
      }
    }
    load();
    
    window.addEventListener('board-event-flow-update', load);
    return () => window.removeEventListener('board-event-flow-update', load);
  }, [boardId]);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>Activity Flow</h2>
        <p className={styles.subtitle}>Live board activity, grouped by operation.</p>
      </div>
      <div className={styles.content} ref={containerRef}>
        {groups.length === 0 ? (
           <p className={styles.empty}>No activity yet.</p>
        ) : (
          groups.map((group, idx) => (
            <div key={group.correlation_id || `group-${idx}`} className={styles.group}>
              {group.correlation_id ? (
                <div className={styles.groupHeader}>
                  <span>Operation</span>
                  <code>{group.correlation_id.slice(0, 8)}</code>
                </div>
              ) : null}
              {group.events.map((event, eIdx) => {
                 const details = describeEvent(event);
                 const guestId = details.guestId || event.payload?.guest_id;
                 const user = onlineUsers.find(u => u.guest_id === guestId);
                 
                 return (
                   <div key={event.id} className={styles.eventItem}>
                     <div className={styles.timeline}>
                        <div className={styles.dot}></div>
                        {(eIdx < group.events.length - 1 || idx < groups.length - 1) && (
                           <div className={styles.line}></div>
                        )}
                     </div>
                     <div className={styles.eventContent}>
                       <div className={styles.eventMeta}>
                          <Badge tone={SOURCE_COLORS[event.source || 'SYSTEM'] || 'neutral'}>
                            {event.source || 'SYSTEM'}
                          </Badge>
                          <span className={styles.time}>
                             {new Date(event.created_at).toLocaleTimeString([], {
                               hour: '2-digit',
                               minute: '2-digit',
                               second: '2-digit',
                             })}
                          </span>
                       </div>
                       <div className={styles.eventTitle}>{details.title}</div>
                       <p className={styles.eventMessage}>{details.message}</p>
                       
                       {user && (
                          <div className={styles.userStamp}>
                             <div 
                                className={styles.miniAvatar}
                                style={{ backgroundColor: user.color, backgroundImage: user.avatar_url ? `url(${user.avatar_url})` : 'none', backgroundSize: 'cover' }}
                             >
                               {!user.avatar_url && user.display_name.charAt(0).toUpperCase()}
                             </div>
                             <span>{user.display_name}</span>
                          </div>
                       )}
                     </div>
                   </div>
                 );
              })}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

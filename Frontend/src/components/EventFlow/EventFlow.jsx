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

function getEventActorId(event) {
  return (
    event.payload?.task?.guest_id ||
    event.payload?.guest_id ||
    event.payload?.notification?.guest_id ||
    event.payload?.incoming_task?.guest_id ||
    null
  );
}

function getOperationSummary(events) {
  const titles = [...new Set(events.map((event) => describeEvent(event).title))];
  if (titles.length === 0) {
    return 'Operation';
  }
  if (titles.length === 1) {
    return titles[0];
  }
  if (titles.length === 2) {
    return `${titles[0]} + ${titles[1]}`;
  }
  return `${titles[0]} and ${titles.length - 1} more`;
}

function buildEventClusters(events, onlineUsers) {
  const usersMap = new Map(onlineUsers.map((user) => [user.guest_id, user]));

  return events.reduce((clusters, event) => {
    const actorId = getEventActorId(event);
    const source = event.source || 'SYSTEM';
    const previousCluster = clusters[clusters.length - 1];

    if (
      previousCluster &&
      previousCluster.actorId &&
      actorId &&
      previousCluster.actorId === actorId &&
      previousCluster.source === source
    ) {
      previousCluster.events.push(event);
      return clusters;
    }

    clusters.push({
      actorId,
      source,
      actor: actorId ? usersMap.get(actorId) || null : null,
      events: [event],
    });
    return clusters;
  }, []);
}

function buildCompactGroups(events, onlineUsers) {
  const clusters = buildEventClusters(events, onlineUsers);
  const grouped = [];

  clusters.forEach((cluster) => {
    const previous = grouped[grouped.length - 1];
    if (
      previous &&
      previous.actorId === cluster.actorId &&
      previous.source === cluster.source
    ) {
      previous.events.push(...cluster.events);
      return;
    }

    grouped.push({ ...cluster, events: [...cluster.events] });
  });

  return grouped;
}

function summarizeEventBatch(events) {
  const titles = [...new Set(events.map((event) => describeEvent(event).title))];
  if (titles.length <= 1) {
    return titles[0] || 'Update';
  }
  if (titles.length === 2) {
    return `${titles[0]} + ${titles[1]}`;
  }
  return `${titles[0]} + ${titles.length - 1} more`;
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
          groups.map((group, idx) => {
            const clusters = buildCompactGroups(group.events, onlineUsers);

            return (
              <div key={group.correlation_id || `group-${idx}`} className={styles.group}>
                <div className={styles.groupHeader}>
                  <div>
                    <span className={styles.groupLabel}>Operation</span>
                    <strong>{getOperationSummary(group.events)}</strong>
                  </div>
                  <div className={styles.groupMeta}>
                    <span>{group.events.length} event{group.events.length === 1 ? '' : 's'}</span>
                    {group.correlation_id ? <code>{group.correlation_id.slice(0, 8)}</code> : null}
                  </div>
                </div>

                {clusters.map((cluster, clusterIndex) => (
                  <div key={`${group.correlation_id || idx}-${clusterIndex}`} className={styles.cluster}>
                    <div className={styles.clusterIntro}>
                      {cluster.actor ? (
                        <div className={styles.userStamp}>
                          <div
                            className={styles.miniAvatar}
                            style={{
                              backgroundColor: cluster.actor.color,
                              backgroundImage: cluster.actor.avatar_url
                                ? `url(${cluster.actor.avatar_url})`
                                : 'none',
                              backgroundSize: 'cover',
                            }}
                          >
                            {!cluster.actor.avatar_url &&
                              cluster.actor.display_name.charAt(0).toUpperCase()}
                          </div>
                          <span>{cluster.actor.display_name}</span>
                        </div>
                      ) : (
                        <div className={styles.userStamp}>
                          <span>System batch</span>
                        </div>
                      )}
                      <Badge tone={SOURCE_COLORS[cluster.source] || 'neutral'}>{cluster.source}</Badge>
                    </div>

                    <div className={styles.eventItem}>
                      <div className={styles.timeline}>
                        <div className={styles.dot}></div>
                        {clusterIndex < clusters.length - 1 || idx < groups.length - 1 ? (
                          <div className={styles.line}></div>
                        ) : null}
                      </div>
                      <div className={styles.eventContent}>
                        <div className={styles.eventMeta}>
                          <span className={styles.time}>
                            {new Date(cluster.events[0].created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                          <span className={styles.count}>
                            {cluster.events.length} action{cluster.events.length === 1 ? '' : 's'}
                          </span>
                        </div>
                        <div className={styles.eventTitle}>{summarizeEventBatch(cluster.events)}</div>
                        <p className={styles.eventMessage}>
                          {cluster.events.map((event) => describeEvent(event).message).join(' ')}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

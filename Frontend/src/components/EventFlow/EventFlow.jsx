import { useEffect, useState, useRef } from 'react';

import { getBoardEvents } from '../../api/boardsApi';
import { useLocale } from '../../contexts/LocaleContext';
import { getAvatarSurfaceStyle } from '../../utils/imagePlaceholders';
import { t } from '../../utils/i18n';
import styles from './EventFlow.module.css';
const COMPACT_GROUP_WINDOW_MS = 90 * 1000;

function describeEvent(event, language) {
  const task = event.payload?.task;
  const notification = event.payload?.notification;
  const incomingTask = event.payload?.incoming_task;
  const rule = event.payload?.rule;
  const message = event.payload?.message;

  if (event.type === 'TASK_CREATED') {
    return {
      title: t('taskCreated', language),
      message: task?.title ? `"${task.title}" ${t('newTaskEnteredBoard', language).toLowerCase()}` : t('newTaskEnteredBoard', language),
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'TASK_UPDATED') {
    return {
      title: t('taskUpdated', language),
      message: task?.title ? `"${task.title}" ${t('taskWasEdited', language).toLowerCase()}` : t('taskWasEdited', language),
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'TASK_MOVED') {
    return {
      title: t('taskMoved', language),
      message: task?.title
        ? `"${task.title}" moved to ${task.status || t('movedToNewColumn', language)}.`
        : t('taskChangedColumn', language),
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'TASK_DELETED') {
    return {
      title: t('taskRemoved', language),
      message: task?.title ? `"${task.title}" ${t('taskLeftBoard', language).toLowerCase()}` : t('taskDeleted', language),
      guestId: task?.guest_id,
    };
  }

  if (event.type === 'NOTIFICATION_CREATED') {
    return {
      title: t('notificationDelivered', language),
      message: notification?.message || notification?.title || t('newNotificationGenerated', language),
    };
  }

  if (event.type === 'INCOMING_TASK_RECEIVED') {
    return {
      title: t('incomingTaskReceived', language),
      message: incomingTask?.external_id
        ? `Payload ${incomingTask.external_id} entered the queue.`
        : t('payloadEnteredQueue', language),
    };
  }

  if (event.type === 'INCOMING_TASK_VALIDATED') {
    return {
      title: t('incomingTaskValidated', language),
      message: t('payloadPassedValidation', language),
    };
  }

  if (event.type === 'INCOMING_TASK_PROCESSED') {
    return {
      title: t('incomingTaskProcessed', language),
      message: task?.title
        ? `Worker turned the payload into "${task.title}".`
        : t('workerCreatedTaskFromPayload', language),
    };
  }

  if (event.type === 'AUTOMATION_TRIGGERED') {
    return {
      title: t('automationTriggered', language),
      message: message || t('ruleReactedToLatestEvent', language),
    };
  }

  if (event.type === 'AUTOMATION_RULE_CREATED') {
    return {
      title: t('ruleCreated', language),
      message: rule?.name ? `"${rule.name}" is now active for this board.` : 'A rule was created.',
    };
  }

  if (event.type === 'AUTOMATION_RULE_UPDATED') {
    return {
      title: t('ruleUpdated', language),
      message: rule?.name ? `"${rule.name}" changed its behavior.` : 'A rule was updated.',
    };
  }

  if (event.type === 'AUTOMATION_RULE_DELETED') {
    return {
      title: t('ruleDeleted', language),
      message: rule?.name ? `"${rule.name}" was removed.` : 'A rule was deleted.',
    };
  }

  return {
    title: event.type.replaceAll('_', ' '),
    message: message || t('systemActivityRecorded', language),
    guestId: task?.guest_id,
  };
}

function getEventActorId(event) {
  return (
    event.payload?.actor?.guest_id ||
    event.payload?.task?.guest_id ||
    event.payload?.guest_id ||
    event.payload?.notification?.guest_id ||
    event.payload?.incoming_task?.guest_id ||
    null
  );
}

function formatEventTime(value) {
  return new Date(value).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function withinCompactWindow(leftEvent, rightEvent) {
  const leftTime = new Date(leftEvent.created_at).getTime();
  const rightTime = new Date(rightEvent.created_at).getTime();
  return Math.abs(leftTime - rightTime) <= COMPACT_GROUP_WINDOW_MS;
}

function getClusterFingerprint(cluster) {
  return `${cluster.actorId || 'system'}:${cluster.source}`;
}

function buildEventClusters(events, onlineUsers, language) {
  const usersMap = new Map(onlineUsers.map((user) => [user.guest_id, user]));

  return events.reduce((clusters, event) => {
    const actorId = getEventActorId(event);
    const source = event.source || 'SYSTEM';
    const details = describeEvent(event, language);
    const actorFromPayload = event.payload?.actor || null;
    const previousCluster = clusters[clusters.length - 1];

    if (
      previousCluster &&
      previousCluster.actorId &&
      actorId &&
      previousCluster.actorId === actorId &&
      previousCluster.source === source &&
      previousCluster.title === details.title
    ) {
      previousCluster.events.push(event);
      return clusters;
    }

    clusters.push({
      actorId,
      source,
      title: details.title,
      actor: actorFromPayload || (actorId ? usersMap.get(actorId) || null : null),
      events: [event],
    });
    return clusters;
  }, []);
}

function buildCompactGroups(events, onlineUsers, language) {
  const clusters = buildEventClusters(events, onlineUsers, language);
  const grouped = [];

  clusters.forEach((cluster) => {
    const previous = grouped[grouped.length - 1];
    if (
      previous &&
      getClusterFingerprint(previous) === getClusterFingerprint(cluster) &&
      withinCompactWindow(previous.events[previous.events.length - 1], cluster.events[0])
    ) {
      previous.events.push(...cluster.events);
      if (!previous.actor && cluster.actor) {
        previous.actor = cluster.actor;
      }
      return;
    }

    grouped.push({ ...cluster, events: [...cluster.events] });
  });

  return grouped;
}

function summarizeEventBatch(events, language) {
  const titles = [...new Set(events.map((event) => describeEvent(event, language).title))];
  if (titles.length <= 1) {
    return titles[0] || t('update', language);
  }
  if (titles.length === 2) {
    return `${titles[0]} + ${titles[1]}`;
  }
  return `${titles[0]} + ${titles.length - 1} ${t('more', language)}`;
}

function summarizeEventMessages(events, language) {
  const messages = [...new Set(events.map((event) => describeEvent(event, language).message))];
  if (messages.length <= 2) {
    return messages.join(' ');
  }
  return `${messages.slice(0, 2).join(' ')} +${messages.length - 2} ${t('moreUpdates', language)}.`;
}

function mergeRenderedGroups(groups, onlineUsers, language) {
  const rendered = [];

  groups.forEach((group) => {
    const clusters = buildCompactGroups(group.events, onlineUsers, language);
    const previous = rendered[rendered.length - 1];
    const firstCluster = clusters[0];
    const previousLastCluster = previous?.clusters?.[previous.clusters.length - 1];

    if (
      previous &&
      previousLastCluster &&
      firstCluster &&
      getClusterFingerprint(previousLastCluster) === getClusterFingerprint(firstCluster) &&
      withinCompactWindow(
        previousLastCluster.events[previousLastCluster.events.length - 1],
        firstCluster.events[0],
      )
    ) {
      previous.events.push(...group.events);
      previous.clusters.push(...clusters);
      return;
    }

    rendered.push({
      key: group.correlation_id || `group-${rendered.length}`,
      correlationId: group.correlation_id,
      events: [...group.events],
      clusters,
    });
  });

  return rendered;
}

export default function EventFlow({ boardId, onlineUsers = [] }) {
  const { language } = useLocale();
  const [groups, setGroups] = useState([]);
  const containerRef = useRef(null);
  const renderedGroups = mergeRenderedGroups(groups, onlineUsers, language);

  useEffect(() => {
    async function load() {
      try {
        const data = await getBoardEvents(boardId);
        setGroups(data);
      } catch (err) {
        console.error(t('failedToLoadEvents', language), err);
      }
    }
    load();
    
    window.addEventListener('board-event-flow-update', load);
    return () => window.removeEventListener('board-event-flow-update', load);
  }, [boardId, language]);

  // Flatten all clusters for compact timeline view with grouping by actor
  const allClusters = renderedGroups.flatMap((g) => g.clusters);
  
  // Group consecutive clusters by actor
  const groupedByActor = [];
  let currentActorGroup = null;
  
  allClusters.forEach((cluster) => {
    const actorId = cluster.actorId || 'system';
    
    if (currentActorGroup?.actorId === actorId && currentActorGroup?.actor?.guest_id === cluster.actor?.guest_id) {
      currentActorGroup.clusters.push(cluster);
    } else {
      currentActorGroup = {
        actorId,
        actor: cluster.actor,
        clusters: [cluster],
        groupIdx: groupedByActor.length,
      };
      groupedByActor.push(currentActorGroup);
    }
  });

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>{t('activity', language)}</h2>
        <p className={styles.subtitle}>
          {allClusters.length} {allClusters.length === 1 ? t('eventCount', language) : t('eventCountMany', language)}
        </p>
      </div>
      <div className={styles.content} ref={containerRef}>
        {allClusters.length === 0 ? (
           <p className={styles.empty}>{t('noActivityYet', language)}</p>
        ) : (
          <div className={styles.timeline}>
            {groupedByActor.map((actorGroup) => (
              <div key={`actor-${actorGroup.groupIdx}`} className={styles.actorGroup}>
                <div className={styles.actorHeader}>
                  {actorGroup.actor ? (
                    <div className={styles.actor}>
                      <div
                        className={styles.avatar}
                        style={getAvatarSurfaceStyle(
                          actorGroup.actor.avatar_url,
                          actorGroup.actor.color,
                        )}
                      >
                        {!actorGroup.actor.avatar_url &&
                          actorGroup.actor.display_name.charAt(0).toUpperCase()}
                      </div>
                      <span className={styles.actorName}>{actorGroup.actor.display_name}</span>
                    </div>
                  ) : (
                    <span className={styles.systemLabel}>{t('system', language)}</span>
                  )}
                </div>
                
                {actorGroup.clusters.map((cluster, clusterIdx) => (
                  <div key={`${actorGroup.groupIdx}-${clusterIdx}`} className={styles.event}>
                    <div className={styles.eventDot}></div>
                    <div className={styles.eventLine}></div>
                    <div className={styles.eventBody}>
                      <div className={styles.eventHeader}>
                        <div className={styles.eventMeta}>
                          <span className={styles.time}>{formatEventTime(cluster.events[0].created_at)}</span>
                          {cluster.events.length > 1 && (
                            <span className={styles.count}>{cluster.events.length}</span>
                          )}
                        </div>
                      </div>
                      <div className={styles.eventText}>
                        <div className={styles.eventTitle}>{summarizeEventBatch(cluster.events, language)}</div>
                        <p className={styles.eventMessage}>{summarizeEventMessages(cluster.events, language)}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

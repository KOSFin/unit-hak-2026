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
    
    // We would ideally listen to WS here to update events live,
    // but the backend WS broadcasts standard `event` messages.
    // For MVP, polling or explicit live updates could be hooked up, 
    // but for now, we'll just fetch initially.
    
    const handleWsEvent = (e) => {
        // Here we could intercept window events if we re-emit from socket
    };
    
    window.addEventListener('board-event-flow-update', load);
    return () => window.removeEventListener('board-event-flow-update', load);
  }, [boardId]);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>Activity Flow</h2>
      </div>
      <div className={styles.content} ref={containerRef}>
        {groups.length === 0 ? (
           <p className={styles.empty}>No activity yet.</p>
        ) : (
          groups.map((group, idx) => (
            <div key={group.correlation_id || `group-${idx}`} className={styles.group}>
              {group.events.map((event, eIdx) => {
                 // Try to map guest_id to online user
                 const guestId = event.payload?.task?.guest_id || event.payload?.guest_id;
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
                             {new Date(event.created_at).toLocaleTimeString()}
                          </span>
                       </div>
                       <div className={styles.eventTitle}>{event.type}</div>
                       
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

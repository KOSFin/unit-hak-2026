import { useState } from 'react';

import Button from '../Ui/Button';
import Input from '../Ui/Input';
import RulesPanel from '../RulesPanel/RulesPanel';
import IncomingTasksPanel from '../IncomingTasksPanel/IncomingTasksPanel';
import styles from './AdminPanel.module.css';

export default function AdminPanel({
  columns,
  rules,
  incomingTasks,
  pending,
  onCreateColumn,
  onRenameColumn,
  onDeleteColumn,
  onCreateRule,
  onToggleRule,
  onDeleteRule,
  onSendDemoTask,
}) {
  const [newColumnTitle, setNewColumnTitle] = useState('');
  const [drafts, setDrafts] = useState({});

  const handleCreateColumn = async () => {
    if (!newColumnTitle.trim()) {
      return;
    }

    await onCreateColumn(newColumnTitle.trim());
    setNewColumnTitle('');
  };

  return (
    <div className={styles.stack}>
      <section className={styles.panel}>
        <div>
          <p className={styles.kicker}>Board setup</p>
          <h2>Columns</h2>
        </div>
        <div className={styles.createRow}>
          <Input
            label="Add column"
            value={newColumnTitle}
            onChange={(event) => setNewColumnTitle(event.target.value)}
            placeholder="Review"
          />
          <Button onClick={handleCreateColumn} disabled={pending}>
            Add
          </Button>
        </div>

        <div className={styles.columns}>
          {columns.map((column) => (
            <div key={column.id} className={styles.columnRow}>
              <Input
                label={column.is_default ? 'Default column' : 'Custom column'}
                value={drafts[column.id] ?? column.title}
                onChange={(event) =>
                  setDrafts((current) => ({ ...current, [column.id]: event.target.value }))
                }
              />
              <div className={styles.rowActions}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onRenameColumn(column.id, drafts[column.id] ?? column.title)}
                  disabled={pending}
                >
                  Save
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onDeleteColumn(column.id)}
                  disabled={pending}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.panel}>
        <RulesPanel
          rules={rules}
          pending={pending}
          onCreateRule={onCreateRule}
          onToggleRule={onToggleRule}
          onDeleteRule={onDeleteRule}
        />
      </section>

      <section className={styles.panel}>
        <IncomingTasksPanel items={incomingTasks} pending={pending} onSendDemoTask={onSendDemoTask} />
      </section>
    </div>
  );
}

import { useState } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
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
  const { language } = useLocale();
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
          <p className={styles.kicker}>{t('boardSetup', language)}</p>
          <h2>{t('columns', language)}</h2>
        </div>
        <div className={styles.createRow}>
          <Input
            label={t('addColumn', language)}
            value={newColumnTitle}
            onChange={(event) => setNewColumnTitle(event.target.value)}
            placeholder={t('addColumnPlaceholder', language)}
          />
          <Button onClick={handleCreateColumn} disabled={pending}>
            {t('add', language)}
          </Button>
        </div>

        <div className={styles.columns}>
          {columns.map((column) => (
            <div key={column.id} className={styles.columnRow}>
              <Input
                label={column.is_default ? t('defaultColumn', language) : t('customColumn', language)}
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
                  {t('save', language)}
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onDeleteColumn(column.id)}
                  disabled={pending}
                >
                  {t('delete', language)}
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

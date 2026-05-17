import { useState } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Button from '../Ui/Button';
import Input from '../Ui/Input';
import RulesPanel from '../RulesPanel/RulesPanel';
import IncomingTasksPanel from '../IncomingTasksPanel/IncomingTasksPanel';
import styles from './AdminPanel.module.css';

export default function AdminPanel({
  board,
  columns,
  rules,
  incomingTasks,
  pending,
  onUpdateBoardSettings,
  canManageBoard,
  onDeleteBoard,
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
  const [activeSection, setActiveSection] = useState('columns');

  const sections = [
    { id: 'columns', label: t('columns', language) },
    { id: 'access', label: t('access', language) },
    { id: 'rules', label: t('rules', language) },
    { id: 'incoming', label: t('incomingTasks', language) },
    { id: 'danger', label: t('dangerZone', language) },
  ];

  const handleCreateColumn = async () => {
    if (!newColumnTitle.trim()) {
      return;
    }

    await onCreateColumn(newColumnTitle.trim());
    setNewColumnTitle('');
  };

  return (
    <div className={styles.stack}>
      <div className={styles.tabs} role="tablist" aria-label={t('adminPanel', language)}>
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            role="tab"
            aria-selected={activeSection === section.id}
            className={`${styles.tab} ${activeSection === section.id ? styles.tabActive : ''}`}
            onClick={() => setActiveSection(section.id)}
          >
            {section.label}
          </button>
        ))}
      </div>

      {activeSection === 'columns' ? (
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
      ) : null}

      {activeSection === 'access' ? (
        <section className={styles.panel}>
          <div>
            <p className={styles.kicker}>{board?.name}</p>
            <h2>{t('adminAccess', language)}</h2>
          </div>

          <div className={styles.accessGrid}>
            <button
              type="button"
              className={`${styles.optionCard} ${!board?.allow_guest_admin ? styles.optionCardActive : ''}`}
              onClick={() => onUpdateBoardSettings?.({ allow_guest_admin: false })}
              disabled={pending || !canManageBoard}
            >
              <strong>{t('creatorOnlyAdmin', language)}</strong>
              <span>{t('creatorOnlyAdminHint', language)}</span>
            </button>

            <button
              type="button"
              className={`${styles.optionCard} ${board?.allow_guest_admin ? styles.optionCardActive : ''}`}
              onClick={() => onUpdateBoardSettings?.({ allow_guest_admin: true })}
              disabled={pending || !canManageBoard}
            >
              <strong>{t('allGuestsAdmin', language)}</strong>
              <span>{t('allGuestsAdminHint', language)}</span>
            </button>
          </div>
        </section>
      ) : null}

      {activeSection === 'rules' ? (
        <section className={styles.panel}>
          <RulesPanel
            rules={rules}
            pending={pending}
            onCreateRule={onCreateRule}
            onToggleRule={onToggleRule}
            onDeleteRule={onDeleteRule}
          />
        </section>
      ) : null}

      {activeSection === 'incoming' ? (
        <section className={styles.panel}>
          <IncomingTasksPanel items={incomingTasks} pending={pending} onSendDemoTask={onSendDemoTask} />
        </section>
      ) : null}

      {activeSection === 'danger' ? (
        <section className={styles.panel}>
          <div>
            <p className={styles.kicker}>{t('dangerZone', language)}</p>
            <h2>{t('deleteBoardForever', language)}</h2>
          </div>

          <div className={styles.dangerCard}>
            <p>{t('deleteBoardDescription', language)}</p>
            <Button variant="danger" onClick={onDeleteBoard} disabled={pending || !canManageBoard}>
              {t('deleteBoardForever', language)}
            </Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}

import { useState } from 'react';

import { useLocale } from '../../contexts/LocaleContext';
import { t } from '../../utils/i18n';
import Button from '../Ui/Button';
import Input from '../Ui/Input';
import Select from '../Ui/Select';
import Textarea from '../Ui/Textarea';
import styles from './RulesPanel.module.css';

const DEFAULT_CONDITION = '{\n  "tag": "urgent"\n}';

export default function RulesPanel({ rules, onCreateRule, onToggleRule, onDeleteRule, pending }) {
  const { language } = useLocale();
  const [name, setName] = useState(t('newAutomationRule', language));
  const [triggerType, setTriggerType] = useState('TASK_ANY');
  const [condition, setCondition] = useState(DEFAULT_CONDITION);
  const [action, setAction] = useState(
    `{\n  "set_priority": "HIGH",\n  "notify": "${t('rulePriorityUrgentNotify', language)}"\n}`,
  );
  const [error, setError] = useState('');

  const handleCreate = async () => {
    try {
      setError('');
      await onCreateRule({
        name,
        enabled: true,
        trigger_type: triggerType,
        condition: JSON.parse(condition),
        action: JSON.parse(action),
      });
    } catch (caughtError) {
      setError(caughtError.message);
    }
  };

  return (
    <section className={styles.panel}>
      <div>
        <p className={styles.kicker}>{t('adminControls', language)}</p>
        <h2>{t('automationRules', language)}</h2>
      </div>

      <div className={styles.list}>
        {rules.map((rule) => (
          <article key={rule.id} className={styles.rule}>
            <div>
              <h3>{rule.name}</h3>
              <p>{rule.trigger_type}</p>
            </div>
            <div className={styles.actions}>
              <Button
                variant={rule.enabled ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => onToggleRule(rule)}
                disabled={pending}
              >
                {rule.enabled ? t('disable', language) : t('enable', language)}
              </Button>
              <Button variant="danger" size="sm" onClick={() => onDeleteRule(rule.id)} disabled={pending}>
                {t('delete', language)}
              </Button>
            </div>
          </article>
        ))}
      </div>

      <div className={styles.form}>
        <Input label={t('ruleName', language)} value={name} onChange={(event) => setName(event.target.value)} />
        <Select label={t('trigger', language)} value={triggerType} onChange={(event) => setTriggerType(event.target.value)}>
          <option value="TASK_ANY">TASK_ANY</option>
          <option value="TASK_CREATED">TASK_CREATED</option>
          <option value="TASK_UPDATED">TASK_UPDATED</option>
          <option value="TASK_MOVED">TASK_MOVED</option>
        </Select>
        <Textarea
          label={t('conditionJSON', language)}
          value={condition}
          onChange={(event) => setCondition(event.target.value)}
        />
        <Textarea label={t('actionJSON', language)} value={action} onChange={(event) => setAction(event.target.value)} />
        {error ? <p className={styles.error}>{error}</p> : null}
        <Button onClick={handleCreate} disabled={pending}>
          {t('createRule', language)}
        </Button>
      </div>
    </section>
  );
}

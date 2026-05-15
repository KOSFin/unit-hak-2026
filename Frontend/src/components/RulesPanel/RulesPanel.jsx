import { useState } from 'react';

import Button from '../Ui/Button';
import Input from '../Ui/Input';
import Select from '../Ui/Select';
import Textarea from '../Ui/Textarea';
import styles from './RulesPanel.module.css';

const DEFAULT_CONDITION = '{\n  "tag": "urgent"\n}';
const DEFAULT_ACTION = '{\n  "set_priority": "HIGH"\n}';

export default function RulesPanel({ rules, onCreateRule, onToggleRule, onDeleteRule, pending }) {
  const [name, setName] = useState('New automation rule');
  const [triggerType, setTriggerType] = useState('TASK_CREATED');
  const [condition, setCondition] = useState(DEFAULT_CONDITION);
  const [action, setAction] = useState(DEFAULT_ACTION);
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
        <p className={styles.kicker}>Admin controls</p>
        <h2>Automation rules</h2>
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
                {rule.enabled ? 'Disable' : 'Enable'}
              </Button>
              <Button variant="danger" size="sm" onClick={() => onDeleteRule(rule.id)} disabled={pending}>
                Delete
              </Button>
            </div>
          </article>
        ))}
      </div>

      <div className={styles.form}>
        <Input label="Rule name" value={name} onChange={(event) => setName(event.target.value)} />
        <Select label="Trigger" value={triggerType} onChange={(event) => setTriggerType(event.target.value)}>
          <option value="TASK_CREATED">TASK_CREATED</option>
          <option value="TASK_UPDATED">TASK_UPDATED</option>
          <option value="TASK_MOVED">TASK_MOVED</option>
        </Select>
        <Textarea
          label="Condition JSON"
          value={condition}
          onChange={(event) => setCondition(event.target.value)}
        />
        <Textarea label="Action JSON" value={action} onChange={(event) => setAction(event.target.value)} />
        {error ? <p className={styles.error}>{error}</p> : null}
        <Button onClick={handleCreate} disabled={pending}>
          Create rule
        </Button>
      </div>
    </section>
  );
}

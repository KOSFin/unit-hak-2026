import json
import logging
import os
import sys
import httpx
from pika.exceptions import AMQPError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.queue.rabbitmq import get_rabbitmq_connection
from app.repositories.rule_repository import AutomationRuleRepository
from app.schemas.event import DomainEventSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_event(ch, method, properties, body):
    try:
        data = json.loads(body)
        event = DomainEventSchema(**data)
        if event.type == "TASK_MOVED":
            handle_task_moved(event)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def handle_task_moved(event: DomainEventSchema):
    if not event.payload or "task" not in event.payload: return
    task = event.payload["task"]
    column_id = task.get("column_id")
    task_id = task.get("id")
    version = task.get("version")
    if not column_id or not task_id: return

    db = SessionLocal()
    try:
        rules = AutomationRuleRepository(db).list_all()
        for rule in rules:
            if rule.enabled and rule.trigger_type == "TASK_MOVED":
                if rule.condition.get("column_id") == column_id:
                    apply_action(task_id, version, rule.action)
    finally:
        db.close()

def apply_action(task_id: str, version: int, action: dict):
    if action.get("type") == "set_status" and action.get("status"):
        url = getattr(get_settings(), "api_url", "http://localhost:8000")
        try:
            httpx.patch(f"{url}/api/tasks/{task_id}", json={"status": action["status"], "version": version}, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to apply rule: {e}")

def main():
    conn = get_rabbitmq_connection()
    if not conn:
        sys.exit(1)
    channel = conn.channel()
    channel.queue_declare(queue="task_events", durable=True)
    channel.queue_bind(exchange="amq.fanout", queue="task_events")
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="task_events", on_message_callback=process_event)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    except Exception as e:
        logger.error(f"Worker crashed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":  # pragma: no cover
    main()


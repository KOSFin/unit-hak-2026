import asyncio
import json
import logging
import threading

from pika.exceptions import AMQPError

from app.queue.rabbitmq import get_rabbitmq_connection
from app.ws.manager import manager

logger = logging.getLogger(__name__)

class WSConsumerThread(threading.Thread):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(daemon=True)
        self.loop = loop
        self.connection = None
        self.channel = None
        self._stop_event = threading.Event()

    def run(self):
        logger.info("Starting WebSocket RabbitMQ consumer thread")
        try:
            self.connection = get_rabbitmq_connection()
            if not self.connection:
                logger.warning("RabbitMQ connection failed. WS consumer disabled.")
                return

            self.channel = self.connection.channel()
            result = self.channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue
            self.channel.queue_bind(exchange="amq.fanout", queue=queue_name)
            self.channel.basic_consume(
                queue=queue_name, on_message_callback=self._on_message, auto_ack=True
            )
            
            while not self._stop_event.is_set():
                self.connection.process_data_events(time_limit=1.0)
        except Exception as e:
            logger.error(f"WS Consumer error: {e}")
        finally:
            self.stop()

    def _on_message(self, ch, method, properties, body):
        try:
            data = json.loads(body)
            # Find board_id from payload if possible
            # But the event structure is generic, e.g. payload: {"task": {"board_id": "xxx"}}
            payload = data.get("payload", {})
            if "task" in payload and "board_id" in payload["task"]:
                board_id = payload["task"]["board_id"]
                # Broadcast the raw event string to the board
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_to_board(board_id, body.decode("utf-8")), self.loop
                )
        except Exception as e:
            logger.error(f"Error processing WS event: {e}")
        finally:
            # Always ack, even if error, because this is just broadcasting to WS.
            # Real business logic is in the worker.
            # Actually, if we use the SAME queue as the worker, we shouldn't steal messages!
            pass

    def stop(self):
        self._stop_event.set()
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
            except Exception:
                pass

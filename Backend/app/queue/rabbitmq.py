import logging
import time

import pika

from app.core.config import get_settings

EVENT_EXCHANGE = "flowboard.events"
logger = logging.getLogger(__name__)

def get_rabbitmq_connection(
    max_attempts: int = 1,
    retry_delay_seconds: float = 0.0,
) -> pika.BlockingConnection | None:
    settings = get_settings()
    if settings.rabbitmq_url:
        params = pika.URLParameters(settings.rabbitmq_url)
    elif settings.rabbitmq_host:
        params = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
        )
    else:
        return None

    attempts = max(1, max_attempts)
    for attempt in range(1, attempts + 1):
        try:
            return pika.BlockingConnection(params)
        except Exception:
            logger.warning(
                "RabbitMQ connection attempt %s/%s failed",
                attempt,
                attempts,
                exc_info=True,
            )
            if attempt >= attempts:
                return None
            if retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)
    return None

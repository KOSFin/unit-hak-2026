import pika

from app.core.config import get_settings

EVENT_EXCHANGE = "flowboard.events"


def get_rabbitmq_connection() -> pika.BlockingConnection | None:
    settings = get_settings()
    try:
        if settings.rabbitmq_url:
            params = pika.URLParameters(settings.rabbitmq_url)
            return pika.BlockingConnection(params)
        if settings.rabbitmq_host:
            params = pika.ConnectionParameters(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
            )
            return pika.BlockingConnection(params)
    except Exception:
        return None
    return None

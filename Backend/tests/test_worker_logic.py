import runpy
from datetime import UTC, datetime

import pytest

from app.models.incoming_task import IncomingTaskStatus
from app.schemas.event import DomainEventSchema
from app.schemas.incoming_task import IncomingTaskCreate
from app.schemas.task import TaskCreate
from app.services.event_service import EventService
from app.services.incoming_task_service import IncomingTaskService
from app.services.task_service import TaskService
from app.worker.main import WorkerEventProcessor, main, process_event


def test_worker_event_processor_task_and_incoming(db_session, seeded_board):
    created_task = TaskService(db_session).create_task(
        TaskCreate(
            board_id=seeded_board["board"].id,
            column_id=seeded_board["todo"].id,
            title="Worker task",
            tags=["urgent"],
        )
    )
    task = EventService(db_session).record_event(
        "TASK_CREATED",
        "task",
        created_task.id,
        {"task": {"id": created_task.id}},
    )

    processor = WorkerEventProcessor(db_session)
    assert processor.process_payload(b"not-json") is False
    assert (
        processor.process_payload(
            {
                "id": "missing",
                "type": "TASK_CREATED",
                "entity_type": "task",
                "payload": {},
                "created_at": datetime.now(UTC).isoformat(),
            }
    )
        is False
    )
    assert processor.process_payload(task.id) is False
    task_schema = DomainEventSchema.model_validate(
        {
            "id": task.id,
            "type": task.type,
            "entity_type": task.entity_type,
            "entity_id": task.entity_id,
            "payload": task.payload,
            "created_at": task.created_at,
        }
    )
    assert processor.process_payload(task_schema.model_dump()) is True

    incoming = IncomingTaskService(db_session).create_task(
        payload=IncomingTaskCreate(
            external_id="in-1",
            raw_payload={"title": "Imported"},
        ),
    )
    incoming_event = EventService(db_session).record_event(
        "INCOMING_TASK_RECEIVED",
        "incoming_task",
        incoming.id,
        {"incoming_task": {"id": incoming.id}},
    )
    incoming_schema = DomainEventSchema.model_validate(
        {
            "id": incoming_event.id,
            "type": incoming_event.type,
            "entity_type": incoming_event.entity_type,
            "entity_id": incoming_event.entity_id,
            "payload": incoming_event.payload,
            "created_at": incoming_event.created_at,
        }
    )
    assert processor.process_payload(incoming_schema.model_dump()) is True
    assert (
        IncomingTaskService(db_session).repo.get_by_id(incoming.id).status
        == IncomingTaskStatus.PROCESSED
    )

    existing = EventService(db_session).repo.get_by_id(incoming_event.id)
    existing.processed = True
    db_session.commit()
    assert processor.process_payload(incoming_schema.model_dump()) is True

    processor._dispatch(
        DomainEventSchema(
            id="noop",
            type="INCOMING_TASK_RECEIVED",
            entity_type="incoming_task",
            entity_id=None,
            payload={},
            created_at=datetime.now(UTC),
        )
    )


def test_worker_dispatch_failure_marks_event(db_session):
    event = EventService(db_session).record_event("TASK_UPDATED", "task", "task-1", {"task": {}})
    processor = WorkerEventProcessor(db_session)
    processor._dispatch = lambda _event: (_ for _ in ()).throw(RuntimeError("boom"))
    assert (
        processor.process_payload(
            {
                "id": event.id,
                "type": event.type,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "payload": event.payload,
                "created_at": event.created_at.isoformat(),
            }
        )
        is False
    )
    assert EventService(db_session).repo.get_by_id(event.id).error == "boom"


def test_process_event_and_worker_main(monkeypatch):
    acked = False
    nacked = False

    class ChannelStub:
        def basic_ack(self, delivery_tag):
            nonlocal acked
            acked = delivery_tag == "tag"

        def basic_nack(self, delivery_tag, requeue):
            nonlocal nacked
            nacked = delivery_tag == "tag" and requeue is False

    class MethodStub:
        delivery_tag = "tag"

    class SessionStub:
        def close(self):
            return None

    class ProcessorStub:
        def __init__(self, _session):
            return None

        def process_payload(self, payload):
            return payload == b"ok"

    monkeypatch.setattr("app.worker.main.SessionLocal", lambda: SessionStub())
    monkeypatch.setattr("app.worker.main.WorkerEventProcessor", ProcessorStub)
    process_event(ChannelStub(), MethodStub(), None, b"ok")
    process_event(ChannelStub(), MethodStub(), None, b"bad")
    assert acked is True
    assert nacked is True

    class ConsumerStub:
        def __init__(self, _queue_name):
            self.closed = False

        def connect(self):
            return False

        def consume(self, _callback):
            return True

        def close(self):
            self.closed = True

    monkeypatch.setattr("app.worker.main.RabbitMQConsumer", ConsumerStub)
    assert main() == 1

    class ConnectedConsumer(ConsumerStub):
        def connect(self):
            return True

    monkeypatch.setattr("app.worker.main.RabbitMQConsumer", ConnectedConsumer)
    assert main() == 0

    class KeyboardConsumer(ConnectedConsumer):
        def consume(self, _callback):
            raise KeyboardInterrupt

    monkeypatch.setattr("app.worker.main.RabbitMQConsumer", KeyboardConsumer)
    assert main() == 0

    class BrokenConsumer(ConnectedConsumer):
        def consume(self, _callback):
            raise RuntimeError("boom")

    monkeypatch.setattr("app.worker.main.RabbitMQConsumer", BrokenConsumer)
    assert main() == 1


def test_worker_entrypoint(monkeypatch):
    monkeypatch.setattr("app.worker.main.main", lambda: 0)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("app.worker.__main__", run_name="__main__")
    assert exc.value.code == 0

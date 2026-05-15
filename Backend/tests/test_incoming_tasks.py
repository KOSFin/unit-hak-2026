from datetime import UTC, datetime

import pytest

from app.models.incoming_task import IncomingTaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.incoming_task import IncomingTaskCreate
from app.services.incoming_task_service import IncomingTaskService


@pytest.mark.anyio
async def test_incoming_tasks_api(async_client):
    response = await async_client.post(
        "/api/incoming-tasks",
        json={"external_id": "ext-1", "raw_payload": {"title": "Imported"}},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "RECEIVED"

    duplicate = await async_client.post(
        "/api/incoming-tasks",
        json={"external_id": "ext-1", "raw_payload": {"title": "Imported"}},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["status"] == "DUPLICATE"

    listed = await async_client.get("/api/incoming-tasks")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_process_incoming_tasks(db_session, seeded_board):
    service = IncomingTaskService(db_session)
    valid = service.create_task(
        payload=IncomingTaskCreate(
            external_id="incoming-1",
            raw_payload={
                "title": "Imported task",
                "description": "from api",
                "tags": ["urgent"],
                "deadline": datetime.now(UTC).isoformat(),
            },
        ),
    )
    processed = service.process_incoming_task(valid.id)
    assert processed.status == IncomingTaskStatus.PROCESSED
    assert len(TaskRepository(db_session).list_by_board(seeded_board["board"].id)) == 1

    invalid = service.create_task(
        payload=IncomingTaskCreate(
            external_id="incoming-2",
            raw_payload={"tags": "not-a-list"},
        ),
    )
    rejected = service.process_incoming_task(invalid.id)
    assert rejected.status == IncomingTaskStatus.REJECTED
    assert service.process_incoming_task("missing") is None
    assert service.list_tasks(status="REJECTED")[0].id == rejected.id

import pytest
from httpx import AsyncClient

from app.models.incoming_task import IncomingTask, IncomingTaskStatus


@pytest.mark.anyio
async def test_incoming_tasks_crud(async_client_with_db: AsyncClient, db_session):
    task = IncomingTask(external_id="ext-1", raw_payload={"data": "test"}, status=IncomingTaskStatus.PENDING)
    db_session.add(task)
    db_session.commit()

    response = await async_client_with_db.get("/api/incoming-tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    response = await async_client_with_db.get("/api/incoming-tasks", params={"task_status": "PENDING"})
    assert response.status_code == 200
    
    response = await async_client_with_db.patch(f"/api/incoming-tasks/{task.id}/accept")
    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"

    response = await async_client_with_db.patch(f"/api/incoming-tasks/{task.id}/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"

    response = await async_client_with_db.patch("/api/incoming-tasks/missing/accept")
    assert response.status_code == 404

    response = await async_client_with_db.patch("/api/incoming-tasks/missing/reject")
    assert response.status_code == 404

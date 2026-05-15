import pytest

from app.models.task import TaskPriority
from app.repositories.task_repository import TaskRepository


@pytest.mark.anyio
async def test_columns_crud(async_client, seeded_board):
    board = seeded_board["board"]

    response = await async_client.post(
        "/api/columns",
        json={"board_id": board.id, "title": "Review"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["position"] == 4

    response = await async_client.patch(
        f"/api/columns/{created['id']}",
        json={"title": "QA"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "QA"

    response = await async_client.delete(f"/api/columns/{created['id']}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


@pytest.mark.anyio
async def test_columns_errors(async_client, db_session, seeded_board):
    response = await async_client.post(
        "/api/columns",
        json={"board_id": "missing", "title": "Nope"},
    )
    assert response.status_code == 404

    response = await async_client.patch("/api/columns/missing", json={"title": "Nope"})
    assert response.status_code == 404

    task_repo = TaskRepository(db_session)
    task_repo.create(
        board_id=seeded_board["board"].id,
        column_id=seeded_board["todo"].id,
        title="Task",
        description=None,
        status="To Do",
        priority=TaskPriority.MEDIUM,
        tags=[],
        deadline=None,
        position=1,
    )
    response = await async_client.delete(f"/api/columns/{seeded_board['todo'].id}")
    assert response.status_code == 409

    response = await async_client.delete("/api/columns/missing")
    assert response.status_code == 404

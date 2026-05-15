import pytest

from app.models.task import TaskPriority
from app.repositories.board_repository import BoardRepository, DEFAULT_BOARD_NAME
from app.repositories.column_repository import ColumnRepository
from app.repositories.event_repository import DomainEventRepository


@pytest.mark.anyio
async def test_tasks_crud_and_events(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    event_repo = DomainEventRepository(db_session)

    board = board_repo.create(DEFAULT_BOARD_NAME)
    column = column_repo.create(board.id, "To Do", 1, True)

    response = await async_client_with_db.post(
        "/api/tasks",
        json={
            "board_id": board.id,
            "column_id": column.id,
            "title": "Task",
            "description": "Desc",
            "priority": "MEDIUM",
            "tags": ["tag"],
        },
    )
    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Task"

    response = await async_client_with_db.get("/api/tasks", params={"board_id": board.id})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await async_client_with_db.get(f"/api/tasks/{task['id']}")
    assert response.status_code == 200

    response = await async_client_with_db.patch(
        f"/api/tasks/{task['id']}",
        json={"title": "Task 2", "version": task["version"]},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["version"] == task["version"] + 1

    response = await async_client_with_db.patch(
        f"/api/tasks/{task['id']}",
        json={"title": "Task 3", "version": task["version"]},
    )
    assert response.status_code == 409

    response = await async_client_with_db.patch(
        f"/api/tasks/{task['id']}/move",
        json={"column_id": column.id, "status": "To Do", "version": updated["version"]},
    )
    assert response.status_code == 200
    moved = response.json()
    assert moved["version"] == updated["version"] + 1

    response = await async_client_with_db.delete(f"/api/tasks/{task['id']}")
    assert response.status_code == 200

    response = await async_client_with_db.delete(f"/api/tasks/{task['id']}")
    assert response.status_code == 404

    events = event_repo.list_unprocessed()
    assert len(events) >= 3


@pytest.mark.anyio
async def test_tasks_move_and_validation_errors(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    column = column_repo.create(board.id, "To Do", 1, True)

    response = await async_client_with_db.post(
        "/api/tasks",
        json={
            "board_id": board.id,
            "column_id": column.id,
            "title": "Task",
            "priority": "LOW",
            "tags": [],
        },
    )
    task = response.json()

    response = await async_client_with_db.patch(
        f"/api/tasks/{task['id']}/move",
        json={"column_id": "missing", "status": "To Do", "version": task["version"]},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tasks_create_invalid_column(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)

    response = await async_client_with_db.post(
        "/api/tasks",
        json={
            "board_id": board.id,
            "column_id": "missing",
            "title": "Task",
            "priority": "LOW",
            "tags": [],
        },
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tasks_update_not_found(async_client_with_db):
    response = await async_client_with_db.patch(
        "/api/tasks/missing",
        json={"title": "Task", "version": 1},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_tasks_get_not_found(async_client_with_db):
    response = await async_client_with_db.get("/api/tasks/missing")
    assert response.status_code == 404

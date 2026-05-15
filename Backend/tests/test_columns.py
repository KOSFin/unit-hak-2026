import pytest

from app.models.task import TaskPriority
from app.repositories.board_repository import BoardRepository, DEFAULT_BOARD_NAME
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository


@pytest.mark.anyio
async def test_columns_crud(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)

    response = await async_client_with_db.post(
        "/api/columns",
        json={"board_id": board.id, "title": "Backlog"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Backlog"
    assert created["position"] == 1

    response = await async_client_with_db.patch(
        f"/api/columns/{created['id']}",
        json={"title": "Doing", "position": 2},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Doing"
    assert updated["position"] == 2

    response = await async_client_with_db.delete(f"/api/columns/{created['id']}")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_columns_delete_conflict(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    task_repo = TaskRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    column = column_repo.create(board.id, "To Do", 1, True)

    task_repo.create(
        board_id=board.id,
        column_id=column.id,
        title="Sample",
        description=None,
        status="To Do",
        priority=TaskPriority.LOW,
        tags=[],
        deadline=None,
        position=1,
    )

    response = await async_client_with_db.delete(f"/api/columns/{column.id}")
    assert response.status_code == 409


@pytest.mark.anyio
async def test_columns_not_found(async_client_with_db):
    response = await async_client_with_db.patch("/api/columns/missing", json={"title": "X"})
    assert response.status_code == 404

    response = await async_client_with_db.delete("/api/columns/missing")
    assert response.status_code == 404

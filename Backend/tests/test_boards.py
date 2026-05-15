import pytest

from app.repositories.board_repository import BoardRepository, DEFAULT_BOARD_NAME
from app.repositories.column_repository import ColumnRepository


@pytest.mark.anyio
async def test_get_default_board_not_found(async_client_with_db):
    response = await async_client_with_db.get("/api/boards/default")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_get_default_board(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    column_repo.create(board.id, "To Do", 1, True)

    response = await async_client_with_db.get("/api/boards/default")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == board.id
    assert len(payload["columns"]) == 1


@pytest.mark.anyio
async def test_get_board_by_id(async_client_with_db, db_session):
    board_repo = BoardRepository(db_session)
    board = board_repo.create("Custom")

    response = await async_client_with_db.get(f"/api/boards/{board.id}")
    assert response.status_code == 200
    assert response.json()["id"] == board.id


@pytest.mark.anyio
async def test_get_board_not_found(async_client_with_db):
    response = await async_client_with_db.get("/api/boards/missing")
    assert response.status_code == 404

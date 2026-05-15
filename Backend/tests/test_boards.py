import pytest

from app.repositories.board_repository import BoardRepository


@pytest.mark.anyio
async def test_get_default_board(async_client, db_session):
    board = BoardRepository(db_session).create("FlowBoard")

    response = await async_client.get("/api/boards/default")
    assert response.status_code == 200
    assert response.json()["id"] == board.id

    response = await async_client.get(f"/api/boards/{board.id}")
    assert response.status_code == 200
    assert response.json()["id"] == board.id


@pytest.mark.anyio
async def test_get_board_not_found(async_client):
    response = await async_client.get("/api/boards/default")
    assert response.status_code == 404

    response = await async_client.get("/api/boards/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Board not found"

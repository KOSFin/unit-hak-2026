import pytest

from app.repositories.board_repository import BoardRepository
from app.repositories.notification_repository import NotificationRepository


@pytest.mark.anyio
async def test_notifications_api(async_client, db_session):
    repo = NotificationRepository(db_session)
    one = repo.create("First", "A", "system", None)
    repo.create("Second", "B", "system", None)

    response = await async_client.get("/api/notifications")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await async_client.patch(f"/api/notifications/{one.id}/read")
    assert response.status_code == 200
    assert response.json()["read"] is True

    unread = await async_client.get("/api/notifications", params={"unread_only": True})
    assert unread.status_code == 200
    assert len(unread.json()) == 1

    mark_all = await async_client.post("/api/notifications/mark-all-read")
    assert mark_all.status_code == 200
    assert mark_all.json()["updated"] == 1

    missing = await async_client.patch("/api/notifications/missing/read")
    assert missing.status_code == 404


@pytest.mark.anyio
async def test_notifications_board_scope(async_client, db_session):
    board_a = BoardRepository(db_session).create("Board A")
    board_b = BoardRepository(db_session).create("Board B")
    repo = NotificationRepository(db_session)

    one = repo.create("Board A", "Only A", "system", None, board_id=board_a.id)
    repo.create("Board B", "Only B", "system", None, board_id=board_b.id)

    listed = await async_client.get("/api/notifications", params={"board_id": board_a.id})
    assert listed.status_code == 200
    assert [item["title"] for item in listed.json()] == ["Board A"]

    wrong_board = await async_client.patch(
        f"/api/notifications/{one.id}/read",
        params={"board_id": board_b.id},
    )
    assert wrong_board.status_code == 404

    mark_all = await async_client.post(
        "/api/notifications/mark-all-read",
        params={"board_id": board_a.id},
    )
    assert mark_all.status_code == 200
    assert mark_all.json()["updated"] == 1

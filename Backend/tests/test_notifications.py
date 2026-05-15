import pytest

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

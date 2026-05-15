import pytest
from httpx import AsyncClient

from app.models.notification import Notification


@pytest.mark.anyio
async def test_notifications_crud(async_client_with_db: AsyncClient, db_session):
    notif = Notification(title="Test", message="Test message", type="info")
    db_session.add(notif)
    db_session.commit()

    response = await async_client_with_db.get("/api/notifications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    
    response = await async_client_with_db.patch(f"/api/notifications/{notif.id}/read")
    assert response.status_code == 200
    assert response.json()["read"] is True

    response = await async_client_with_db.patch("/api/notifications/missing/read")
    assert response.status_code == 404

    from app.services.notification_service import NotificationService
    service = NotificationService(db_session)
    service.create_notification("Title", "Hello", "alert")
    
    response = await async_client_with_db.get("/api/notifications", params={"unread_only": True})
    assert response.status_code == 200

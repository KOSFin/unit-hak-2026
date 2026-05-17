from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import get_engine, get_session
from app.main import create_app
from app.repositories.board_repository import BoardRepository
from app.services.cleanup_service import CleanupService

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wm7M1cAAAAASUVORK5CYII="
)


def make_client(monkeypatch, sqlite_engine, db_session, **env) -> TestClient:
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))
    get_settings.cache_clear()
    application = create_app()

    def override_get_session():
        yield db_session

    def override_get_engine():
        return sqlite_engine

    application.dependency_overrides[get_session] = override_get_session
    application.dependency_overrides[get_engine] = override_get_engine
    return TestClient(application)


def test_upload_accepts_image_and_rejects_bad_inputs(monkeypatch, sqlite_engine, db_session, tmp_path):
    with make_client(
        monkeypatch,
        sqlite_engine,
        db_session,
        UPLOADS_PATH=tmp_path,
        MAX_UPLOAD_SIZE_BYTES=1024,
    ) as client:
        uploaded = client.post(
            "/api/uploads",
            files={"file": ("avatar.png", PNG_1X1, "image/png")},
        )
        assert uploaded.status_code == 200
        assert uploaded.json()["url"].startswith("/uploads/")
        saved_name = uploaded.json()["url"].split("/")[-1]
        assert (tmp_path / saved_name).exists()

        invalid = client.post(
            "/api/uploads",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
        assert invalid.status_code == 400

    with make_client(
        monkeypatch,
        sqlite_engine,
        db_session,
        UPLOADS_PATH=tmp_path,
        MAX_UPLOAD_SIZE_BYTES=10,
    ) as client:
        oversized = client.post(
            "/api/uploads",
            files={"file": ("avatar.png", PNG_1X1 * 20, "image/png")},
        )
        assert oversized.status_code == 413


def test_guest_profile_create_and_update(monkeypatch, sqlite_engine, db_session):
    with make_client(monkeypatch, sqlite_engine, db_session) as client:
        created = client.post(
            "/api/guests/profile",
            json={
                "guest_id": "guest-1",
                "display_name": "Guest 1",
                "color": "#111111",
                "avatar_url": "/uploads/avatar.png",
            },
        )
        assert created.status_code == 201
        assert created.json()["display_name"] == "Guest 1"

        updated = client.put(
            "/api/guests/guest-1/profile",
            json={
                "guest_id": "guest-1",
                "display_name": "Guest Edited",
                "color": "#222222",
                "avatar_url": "/uploads/avatar-2.png",
            },
        )
        assert updated.status_code == 200
        assert updated.json()["guest_id"] == "guest-1"
        assert updated.json()["display_name"] == "Guest Edited"

        mismatch = client.put(
            "/api/guests/guest-1/profile",
            json={"guest_id": "guest-2", "display_name": "Mismatch"},
        )
        assert mismatch.status_code == 422


def test_cleanup_inactive_boards_removes_files(monkeypatch, db_session, tmp_path):
    monkeypatch.setenv("UPLOADS_PATH", str(tmp_path))
    get_settings.cache_clear()

    board = BoardRepository(db_session).create(
        "Old board",
        image_path="/uploads/old-board.png",
    )
    board.last_activity_at = datetime.now(UTC) - timedelta(days=10)
    db_session.commit()

    file_path = Path(tmp_path) / "old-board.png"
    file_path.write_bytes(PNG_1X1)

    removed = CleanupService(db_session).cleanup_inactive_boards(3)

    assert removed == 1
    assert BoardRepository(db_session).get_by_id(board.id) is None
    assert not file_path.exists()

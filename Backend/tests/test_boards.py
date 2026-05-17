from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.board import Board


def test_create_board(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/boards", json={"name": "New Board", "retention_days": 3})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Board"
    assert "public_id" in data
    assert data["retention_days"] == 3


def test_create_board_invalid_retention(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/boards", json={"name": "New Board", "retention_days": 7})
    assert response.status_code == 422


def test_get_board_by_public_id(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/boards", json={"name": "Public Board", "retention_days": 3})
    assert response.status_code == 201
    public_id = response.json()["public_id"]

    response = client.get(f"/api/boards/{public_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Public Board"
    assert data["public_id"] == public_id
    assert "columns" in data
    assert len(data["columns"]) == 3


def test_get_board_events(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/boards", json={"name": "Events Board", "retention_days": 3})
    assert response.status_code == 201
    public_id = response.json()["public_id"]
    board_id = response.json()["id"]

    # trigger event
    col = response.json()["columns"][0]
    client.post(f"/api/tasks?board_id={board_id}", json={
        "board_id": board_id, "column_id": col["id"], "title": "Test Task"
    })

    response = client.get(f"/api/boards/{public_id}/events")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

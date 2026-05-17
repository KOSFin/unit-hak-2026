from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.board import Board


def test_create_board(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/api/boards",
        json={
            "name": "New Board",
            "retention_days": 3,
            "image_path": "/uploads/board-logo.png",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Board"
    assert "public_id" in data
    assert data["retention_days"] == 3
    assert data["image_path"] == "/uploads/board-logo.png"
    assert data["board_url"].endswith(f"/board/{data['public_id']}")


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
    assert data["board_url"].endswith(f"/board/{public_id}")
    assert "columns" in data
    assert len(data["columns"]) == 3


def test_update_board_image_path(client: TestClient, db_session: Session) -> None:
    created = client.post("/api/boards", json={"name": "Brand Board", "retention_days": 3})
    assert created.status_code == 201
    public_id = created.json()["public_id"]

    response = client.patch(
        f"/api/boards/{public_id}",
        json={"image_path": "/uploads/new-logo.png"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_path"] == "/uploads/new-logo.png"


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


def test_board_data_is_isolated_by_board_id(client: TestClient, db_session: Session) -> None:
    board_a = client.post("/api/boards", json={"name": "Board A", "retention_days": 3}).json()
    board_b = client.post("/api/boards", json={"name": "Board B", "retention_days": 3}).json()

    todo_a = board_a["columns"][0]["id"]
    todo_b = board_b["columns"][0]["id"]

    task_a = client.post(
        "/api/tasks",
        json={"board_id": board_a["id"], "column_id": todo_a, "title": "Only A"},
    )
    task_b = client.post(
        "/api/tasks",
        json={"board_id": board_b["id"], "column_id": todo_b, "title": "Only B"},
    )

    assert task_a.status_code == 201
    assert task_b.status_code == 201

    listed_a = client.get("/api/tasks", params={"board_id": board_a["id"]})
    listed_b = client.get("/api/tasks", params={"board_id": board_b["id"]})

    assert [task["title"] for task in listed_a.json()] == ["Only A"]
    assert [task["title"] for task in listed_b.json()] == ["Only B"]

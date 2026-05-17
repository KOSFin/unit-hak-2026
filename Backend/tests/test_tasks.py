from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.task import Task


def test_create_task(client: TestClient, db_session: Session) -> None:
    board_res = client.post("/api/boards", json={"name": "Task Board", "retention_days": 3})
    board_id = board_res.json()["id"]
    public_id = board_res.json()["public_id"]
    
    col_res = client.get(f"/api/boards/{public_id}")
    col_id = col_res.json()["columns"][0]["id"]
    
    task_res = client.post("/api/tasks", json={
        "board_id": board_id,
        "column_id": col_id,
        "title": "A Task",
        "guest_id": "g123",
        "correlation_id": "corr1"
    })
    
    assert task_res.status_code == 201
    assert task_res.json()["guest_id"] == "g123"
    assert task_res.json()["correlation_id"] == "corr1"
    
def test_update_task(client: TestClient, db_session: Session) -> None:
    board_res = client.post("/api/boards", json={"name": "Task Board", "retention_days": 3})
    board_id = board_res.json()["id"]
    public_id = board_res.json()["public_id"]
    col_id = client.get(f"/api/boards/{public_id}").json()["columns"][0]["id"]
    
    task = client.post("/api/tasks", json={
        "board_id": board_id, "column_id": col_id, "title": "A Task"
    }).json()
    
    update_res = client.patch(f"/api/tasks/{task['id']}", json={
        "title": "Updated", "version": task["version"], "guest_id": "g456"
    })
    
    assert update_res.status_code == 200
    assert update_res.json()["guest_id"] == "g456"


def test_move_task_rejects_column_from_another_board(client: TestClient, db_session: Session) -> None:
    board_a = client.post("/api/boards", json={"name": "Board A", "retention_days": 3}).json()
    board_b = client.post("/api/boards", json={"name": "Board B", "retention_days": 3}).json()

    task = client.post(
        "/api/tasks",
        json={
            "board_id": board_a["id"],
            "column_id": board_a["columns"][0]["id"],
            "title": "A Task",
        },
    ).json()

    move_res = client.patch(
        f"/api/tasks/{task['id']}/move",
        json={
            "column_id": board_b["columns"][0]["id"],
            "version": task["version"],
        },
    )

    assert move_res.status_code == 404

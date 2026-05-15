import pytest

from app.repositories.event_repository import DomainEventRepository


@pytest.mark.anyio
async def test_tasks_crud_and_conflict(async_client, db_session, seeded_board):
    board = seeded_board["board"]
    todo = seeded_board["todo"]
    in_progress = seeded_board["in_progress"]

    response = await async_client.post(
        "/api/tasks",
        json={
            "board_id": board.id,
            "column_id": todo.id,
            "title": "Build API",
            "tags": ["urgent"],
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["position"] == 1
    assert created["version"] == 1

    response = await async_client.get("/api/tasks", params={"board_id": board.id})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await async_client.get(f"/api/tasks/{created['id']}")
    assert response.status_code == 200

    response = await async_client.patch(
        f"/api/tasks/{created['id']}",
        json={"title": "Build better API", "version": 1},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Build better API"
    assert updated["version"] == 2

    response = await async_client.patch(
        f"/api/tasks/{created['id']}/move",
        json={"column_id": in_progress.id, "version": 2},
    )
    assert response.status_code == 200
    moved = response.json()
    assert moved["column_id"] == in_progress.id
    assert moved["version"] == 3

    conflict = await async_client.patch(
        f"/api/tasks/{created['id']}",
        json={"title": "Outdated", "version": 1},
    )
    assert conflict.status_code == 409

    deleted = await async_client.delete(f"/api/tasks/{created['id']}")
    assert deleted.status_code == 200

    missing = await async_client.get(f"/api/tasks/{created['id']}")
    assert missing.status_code == 404

    events = DomainEventRepository(db_session).list_unprocessed()
    assert len(events) == 4


@pytest.mark.anyio
async def test_task_errors(async_client, seeded_board):
    board = seeded_board["board"]

    response = await async_client.post(
        "/api/tasks",
        json={"board_id": board.id, "column_id": "missing", "title": "Broken"},
    )
    assert response.status_code == 404

    response = await async_client.patch("/api/tasks/missing", json={"title": "Nope", "version": 1})
    assert response.status_code == 404

    response = await async_client.patch(
        "/api/tasks/missing/move",
        json={"column_id": seeded_board["todo"].id, "version": 1},
    )
    assert response.status_code == 404

    response = await async_client.post(
        "/api/tasks",
        json={
            "board_id": board.id,
            "column_id": seeded_board["todo"].id,
            "title": "Existing",
            "position": 5,
        },
    )
    created = response.json()
    response = await async_client.patch(
        f"/api/tasks/{created['id']}/move",
        json={"column_id": "missing", "version": created["version"]},
    )
    assert response.status_code == 404

    response = await async_client.patch(
        f"/api/tasks/{created['id']}/move",
        json={"column_id": seeded_board["todo"].id, "version": 999},
    )
    assert response.status_code == 409

    response = await async_client.delete("/api/tasks/missing")
    assert response.status_code == 404

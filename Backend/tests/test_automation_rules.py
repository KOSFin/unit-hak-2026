import pytest


@pytest.mark.anyio
async def test_automation_rules_api(async_client):
    payload = {
        "name": "Urgent priority",
        "enabled": True,
        "trigger_type": "TASK_CREATED",
        "condition": {"tag": "urgent"},
        "action": {"set_priority": "HIGH"},
    }
    response = await async_client.post("/api/automation-rules", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Urgent priority"

    response = await async_client.get("/api/automation-rules")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await async_client.patch(
        f"/api/automation-rules/{created['id']}",
        json={"enabled": False},
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    response = await async_client.delete(f"/api/automation-rules/{created['id']}")
    assert response.status_code == 200

    missing = await async_client.patch("/api/automation-rules/missing", json={"enabled": True})
    assert missing.status_code == 404

    missing = await async_client.delete("/api/automation-rules/missing")
    assert missing.status_code == 404

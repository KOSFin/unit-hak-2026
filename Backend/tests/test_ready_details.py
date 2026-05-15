from app.core import health as health_module


def test_readiness_status_structure(sqlite_engine):
    status = health_module.readiness_status(sqlite_engine)
    assert "ready" in status
    assert "checks" in status
    assert set(status["checks"]) == {"database", "rabbitmq"}

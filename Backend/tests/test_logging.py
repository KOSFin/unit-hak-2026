import logging

from app.core.logging import setup_logging


def test_setup_logging(monkeypatch):
    captured = {}

    def fake_basic_config(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)
    setup_logging("warning")

    assert captured["level"] == logging.WARNING
    assert "%(message)s" in captured["format"]
    assert captured["force"] is True

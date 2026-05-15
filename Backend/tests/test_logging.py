import logging

from app.core.logging import setup_logging


def test_setup_logging_sets_level():
    setup_logging("debug")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

from app.models.task import TaskPriority
from app.models.incoming_task import IncomingTaskStatus


def test_task_priority_enum_values():
    assert TaskPriority.HIGH.value == "HIGH"


def test_incoming_status_enum_values():
    assert IncomingTaskStatus.DUPLICATE.value == "DUPLICATE"

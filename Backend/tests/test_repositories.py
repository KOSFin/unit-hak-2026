from datetime import UTC, datetime

from app.models.incoming_task import IncomingTaskStatus
from app.models.task import TaskPriority
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.event_repository import DomainEventRepository
from app.repositories.incoming_task_repository import IncomingTaskRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.rule_repository import AutomationRuleRepository
from app.repositories.task_repository import TaskRepository


def test_repositories_crud(db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    task_repo = TaskRepository(db_session)
    event_repo = DomainEventRepository(db_session)
    rule_repo = AutomationRuleRepository(db_session)
    notification_repo = NotificationRepository(db_session)
    incoming_repo = IncomingTaskRepository(db_session)

    board = board_repo.create("FlowBoard")
    assert board_repo.get_default() == board
    assert board_repo.get_by_id(board.id) == board
    assert board_repo.list_all() == [board]
    assert board_repo.update_name(board.id, "Renamed").name == "Renamed"
    assert board_repo.update_name("missing", "Nope") is None

    todo = column_repo.create(board.id, "To Do", 1, True)
    done = column_repo.create(board.id, "Done", 2, False)
    assert column_repo.get_by_title(board.id, "Done") == done
    assert column_repo.get_max_position(board.id) == 2
    assert column_repo.update(done.id, title="Finished").title == "Finished"

    task = task_repo.create(
        board_id=board.id,
        column_id=todo.id,
        title="Task",
        description="Desc",
        status="To Do",
        priority=TaskPriority.MEDIUM,
        tags=["bug"],
        deadline=None,
        position=1,
    )
    assert task_repo.get_by_id(task.id) == task
    assert task_repo.list_by_board(board.id) == [task]
    assert task_repo.list_all() == [task]
    assert task_repo.get_max_position(board.id, todo.id) == 1
    assert task_repo.count_by_column(todo.id) == 1
    assert task_repo.update(task.id, title="Updated").title == "Updated"

    event = event_repo.create("TASK_CREATED", "task", task.id, {"task": {"id": task.id}})
    assert event_repo.list_unprocessed() == [event]
    assert event_repo.mark_processed(event.id).processed is True
    assert event_repo.mark_failed(event.id, "boom").error == "boom"
    assert event_repo.mark_processed("missing") is None
    assert event_repo.mark_failed("missing", "boom") is None

    rule = rule_repo.create("Rule", True, "TASK_CREATED", {"tag": "urgent"}, {"notify": True})
    assert rule_repo.get_by_id(rule.id) == rule
    assert rule_repo.list_all() == [rule]
    assert rule_repo.update(rule.id, enabled=False).enabled is False

    one = notification_repo.create("One", "Message", "system", task.id)
    notification_repo.create("Two", "Message", "system", None)
    assert notification_repo.get_by_id(one.id) == one
    assert len(notification_repo.list_all()) == 2
    assert notification_repo.mark_read(one.id).read is True
    assert notification_repo.mark_all_read() == 1

    incoming = incoming_repo.create("ext-1", {"title": "Task"}, IncomingTaskStatus.RECEIVED)
    assert incoming_repo.get_by_id(incoming.id) == incoming
    assert incoming_repo.get_by_external_id("ext-1") == incoming
    assert incoming_repo.list_all() == [incoming]
    processed = incoming_repo.update_status(
        incoming.id,
        IncomingTaskStatus.PROCESSED,
        processed_at=datetime.now(UTC),
    )
    assert processed.status == IncomingTaskStatus.PROCESSED

    assert task_repo.delete(task.id) is True
    assert task_repo.delete("missing") is False
    assert task_repo.update("missing", title="Nope") is None
    assert column_repo.delete(todo.id) is True
    assert column_repo.delete("missing") is False
    assert notification_repo.mark_read("missing") is None
    assert incoming_repo.update_status("missing", IncomingTaskStatus.REJECTED) is None
    assert rule_repo.delete(rule.id) is True
    assert rule_repo.delete("missing") is False
    assert board_repo.delete(board.id) is True
    assert board_repo.delete("missing") is False

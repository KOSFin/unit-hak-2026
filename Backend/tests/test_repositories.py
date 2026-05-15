from datetime import datetime, timezone

from app.models.incoming_task import IncomingTaskStatus
from app.models.task import TaskPriority
from app.repositories.board_repository import BoardRepository, DEFAULT_BOARD_NAME
from app.repositories.column_repository import ColumnRepository
from app.repositories.event_repository import DomainEventRepository
from app.repositories.incoming_task_repository import IncomingTaskRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.rule_repository import AutomationRuleRepository
from app.repositories.task_repository import TaskRepository


def test_board_repository_crud(db_session):
    repo = BoardRepository(db_session)
    assert repo.get_default() is None

    board = repo.create(DEFAULT_BOARD_NAME)
    assert repo.get_by_id(board.id) is not None
    assert repo.get_by_name(DEFAULT_BOARD_NAME) is not None
    assert repo.get_default() is not None

    all_boards = repo.list_all()
    assert len(all_boards) == 1

    updated = repo.update_name(board.id, "New Board")
    assert updated is not None
    assert updated.name == "New Board"

    missing = repo.update_name("missing", "Nope")
    assert missing is None

    assert repo.delete(board.id) is True
    assert repo.delete("missing") is False


def test_column_repository_crud(db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)

    assert column_repo.get_max_position(board.id) == 0

    column = column_repo.create(board.id, "To Do", 1, True)
    assert column_repo.get_by_id(column.id) is not None

    assert column_repo.get_max_position(board.id) == 1

    columns = column_repo.list_by_board(board.id)
    assert len(columns) == 1

    updated = column_repo.update(column.id, title="Doing", position=2, is_default=False)
    assert updated is not None
    assert updated.title == "Doing"

    missing_update = column_repo.update("missing", title="Nope")
    assert missing_update is None

    assert column_repo.delete(column.id) is True
    assert column_repo.delete("missing") is False


def test_task_repository_crud(db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    task_repo = TaskRepository(db_session)

    board = board_repo.create(DEFAULT_BOARD_NAME)
    column = column_repo.create(board.id, "To Do", 1, True)

    assert task_repo.get_max_position(board.id, column.id) == 0
    assert task_repo.count_by_column(column.id) == 0

    task = task_repo.create(
        board_id=board.id,
        column_id=column.id,
        title="Sample",
        description=None,
        status="To Do",
        priority=TaskPriority.LOW,
        tags=["sample"],
        deadline=None,
        position=1,
    )
    assert task_repo.get_by_id(task.id) is not None

    assert task_repo.get_max_position(board.id, column.id) == 1
    assert task_repo.count_by_column(column.id) == 1

    tasks = task_repo.list_by_board(board.id)
    assert len(tasks) == 1

    updated = task_repo.update(task.id, title="Updated")
    assert updated is not None
    assert updated.title == "Updated"

    assert task_repo.delete(task.id) is True
    assert task_repo.delete("missing") is False

    missing = task_repo.update("missing", title="Nope")
    assert missing is None


def test_event_repository_flow(db_session):
    repo = DomainEventRepository(db_session)
    event = repo.create("TASK_CREATED", "task", "t1", {"foo": "bar"})

    unprocessed = repo.list_unprocessed()
    assert len(unprocessed) == 1

    processed = repo.mark_processed(event.id)
    assert processed is not None
    assert processed.processed is True
    assert processed.processed_at is not None

    missing_processed = repo.mark_processed("missing")
    assert missing_processed is None

    failure = repo.mark_failed("missing", "error")
    assert failure is None

    event2 = repo.create("TASK_UPDATED", "task", "t2", {"foo": "baz"})
    failed = repo.mark_failed(event2.id, "boom")
    assert failed is not None
    assert failed.error == "boom"


def test_rule_repository_crud(db_session):
    repo = AutomationRuleRepository(db_session)
    rule = repo.create("Rule", True, "task.tag", {"tag": "urgent"}, {"notify": "ok"})

    rules = repo.list_all()
    assert len(rules) == 1

    updated = repo.update(rule.id, enabled=False, name="Rule 2")
    assert updated is not None
    assert updated.enabled is False

    missing_update = repo.update("missing", enabled=True)
    assert missing_update is None

    assert repo.delete(rule.id) is True
    assert repo.delete("missing") is False


def test_notification_repository_flow(db_session):
    repo = NotificationRepository(db_session)
    one = repo.create("Title", "Message", "system", None)
    two = repo.create("Title 2", "Message 2", "system", None)

    all_items = repo.list_all()
    assert len(all_items) == 2

    updated = repo.mark_read(one.id)
    assert updated is not None
    assert updated.read is True

    missing = repo.mark_read("missing")
    assert missing is None

    count = repo.mark_all_read()
    assert count >= 1


def test_incoming_task_repository_flow(db_session):
    repo = IncomingTaskRepository(db_session)
    incoming = repo.create("ext-1", {"title": "Incoming"}, IncomingTaskStatus.RECEIVED)

    by_external = repo.get_by_external_id("ext-1")
    assert by_external is not None

    all_items = repo.list_all()
    assert len(all_items) == 1

    processed = repo.update_status(
        incoming.id,
        IncomingTaskStatus.PROCESSED,
        validation_error=None,
        processed_at=datetime.now(timezone.utc),
    )
    assert processed is not None
    assert processed.status == IncomingTaskStatus.PROCESSED

    missing = repo.update_status("missing", IncomingTaskStatus.REJECTED)
    assert missing is None

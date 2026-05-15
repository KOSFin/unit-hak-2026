from datetime import UTC, datetime, timedelta

import pytest

from app.models.incoming_task import IncomingTaskStatus
from app.models.task import TaskPriority
from app.repositories.event_repository import DomainEventRepository
from app.schemas.automation_rule import AutomationRuleCreate, AutomationRuleUpdate
from app.schemas.column import ColumnCreate, ColumnUpdate
from app.schemas.incoming_task import IncomingTaskCreate
from app.schemas.task import TaskCreate, TaskMove, TaskUpdate
from app.services.automation_rule_service import AutomationRuleService
from app.services.automation_service import AutomationService
from app.services.board_service import BoardService
from app.services.column_service import ColumnHasTasksError, ColumnService
from app.services.event_service import EventService, get_publisher
from app.services.incoming_task_service import IncomingTaskService, serialize_incoming_task
from app.services.notification_service import NotificationService
from app.services.seed_service import seed_demo_data
from app.services.task_service import TaskService, VersionConflictError, serialize_task


def test_board_column_and_task_services(db_session, seeded_board):
    board = seeded_board["board"]
    todo = seeded_board["todo"]
    done = seeded_board["done"]

    board_service = BoardService(db_session)
    assert board_service.get_default_board() == board
    assert board_service.get_board(board.id) == board
    assert len(board_service.list_columns(board.id)) == 3

    column_service = ColumnService(db_session)
    created = column_service.create_column(ColumnCreate(board_id=board.id, title="QA"))
    assert created.position == 4
    assert column_service.update_column(created.id, ColumnUpdate(title="Review")).title == "Review"
    assert column_service.update_column(created.id, ColumnUpdate()) == created
    assert column_service.update_column("missing", ColumnUpdate(title="Nope")) is None
    positioned = column_service.create_column(
        ColumnCreate(board_id=board.id, title="Pinned", position=8),
    )
    assert positioned.position == 8

    task_service = TaskService(db_session)
    task = task_service.create_task(
        TaskCreate(
            board_id=board.id,
            column_id=todo.id,
            title="Task",
            tags=["urgent"],
        )
    )
    assert serialize_task(task)["title"] == "Task"
    assert task_service.list_tasks(board.id) == [task]
    assert task_service.get_task(task.id) == task
    updated = task_service.update_task(task.id, TaskUpdate(title="Updated", version=1))
    assert updated.title == "Updated"
    assert task_service.update_task(task.id, TaskUpdate(version=2)) == updated
    with pytest.raises(VersionConflictError):
        task_service.update_task(task.id, TaskUpdate(title="Nope", version=1))

    moved = task_service.move_task(task.id, TaskMove(column_id=done.id, version=2))
    assert moved.column_id == done.id
    assert task_service.delete_task(task.id) is True
    assert task_service.delete_task(task.id) is False

    with pytest.raises(ValueError):
        task_service.create_task(TaskCreate(board_id="missing", column_id=todo.id, title="Bad"))

    another = task_service.create_task(
        TaskCreate(board_id=board.id, column_id=todo.id, title="Task 2"),
    )
    with pytest.raises(ValueError):
        task_service.move_task(another.id, TaskMove(column_id="missing", version=1))

    with pytest.raises(ColumnHasTasksError):
        column_service.delete_column(todo.id)

    assert column_service.delete_column(created.id) is True
    assert column_service.delete_column(positioned.id) is True


def test_event_notification_rule_seed_and_automation_services(
    db_session,
    seeded_board,
    monkeypatch,
):
    board = seeded_board["board"]
    todo = seeded_board["todo"]
    in_progress = seeded_board["in_progress"]

    task = TaskService(db_session).create_task(
        TaskCreate(
            board_id=board.id,
            column_id=todo.id,
            title="Urgent task",
            tags=["urgent", "auto-progress"],
            deadline=datetime.now(UTC) + timedelta(hours=2),
        )
    )

    notification_service = NotificationService(db_session)
    notification = notification_service.create_notification("Title", "Message", "system", task.id)
    assert notification_service.mark_as_read(notification.id).read is True
    assert notification_service.mark_all_as_read() == 0
    plain = notification_service.create_notification("Plain", "Message", "system", None)
    assert plain.task_id is None

    service = AutomationRuleService(db_session)
    rule = service.create_rule(
        AutomationRuleCreate(
            name="Rule",
            enabled=True,
            trigger_type="TASK_CREATED",
            condition={},
            action={},
        )
    )
    assert service.list_rules() == [rule]
    assert service.update_rule(rule.id, AutomationRuleUpdate(enabled=False)).enabled is False
    assert service.update_rule(rule.id, AutomationRuleUpdate()) == rule
    assert service.update_rule("missing", AutomationRuleUpdate(enabled=True)) is None
    assert service.delete_rule(rule.id) is True
    assert service.delete_rule("missing") is False

    automation = AutomationService(db_session)
    updated = automation.apply_task_automations(task.id, "TASK_CREATED")
    assert updated.priority == TaskPriority.HIGH
    assert updated.column_id == in_progress.id
    assert "deadline-soon" in updated.tags
    assert automation.apply_task_automations("missing", "TASK_CREATED") is None
    TaskService(db_session).move_task(
        task.id,
        TaskMove(column_id=seeded_board["done"].id, version=updated.version),
    )
    automation.apply_task_automations(task.id, "TASK_MOVED")
    done_task = TaskService(db_session).create_task(
        TaskCreate(
            board_id=board.id,
            column_id=seeded_board["done"].id,
            title="Done task",
        )
    )
    automation.apply_task_automations(done_task.id, "TASK_MOVED")
    in_progress_task = TaskService(db_session).create_task(
        TaskCreate(
            board_id=board.id,
            column_id=in_progress.id,
            title="Already moving",
            tags=["auto-progress"],
        )
    )
    automation.apply_task_automations(in_progress_task.id, "TASK_CREATED")

    payload = get_publisher()
    assert hasattr(payload, "published_events")

    event = EventService(db_session).record_event("CUSTOM", "task", task.id, {"board_id": board.id})
    assert event.id

    import app.services.event_service as event_module

    event_module._publisher = None

    class ProdSettings:
        app_env = "production"

    monkeypatch.setattr("app.services.event_service.get_settings", lambda: ProdSettings())
    publisher_stub = type("Publisher", (), {"publish": lambda self, event: None})()
    monkeypatch.setattr("app.services.event_service.RabbitMQPublisher", lambda: publisher_stub)
    assert get_publisher() is publisher_stub
    event_module._publisher = None

    seeded = seed_demo_data(db_session)
    assert seeded["rules_created"] >= 0
    seeded_again = seed_demo_data(db_session)
    assert seeded_again["tasks_created"] == 0

    incoming = IncomingTaskService(db_session).create_task(
        IncomingTaskCreate(
            external_id="ext-1",
            raw_payload={"title": "Imported"},
        ),
    )
    assert serialize_incoming_task(incoming)["external_id"] == "ext-1"
    duplicate = IncomingTaskService(db_session).create_task(
        IncomingTaskCreate(
            external_id="ext-1",
            raw_payload={"title": "Imported"},
        ),
    )
    assert duplicate.status == IncomingTaskStatus.DUPLICATE
    assert DomainEventRepository(db_session).get_by_id(event.id) is not None

    invalid_title = IncomingTaskService(db_session).create_task(
        IncomingTaskCreate(external_id="ext-2", raw_payload={}),
    )
    invalid_title_result = IncomingTaskService(db_session).process_incoming_task(invalid_title.id)
    assert invalid_title_result.status == IncomingTaskStatus.REJECTED

    invalid_tags = IncomingTaskService(db_session).create_task(
        IncomingTaskCreate(
            external_id="ext-3",
            raw_payload={"title": "Imported", "tags": [1]},
        ),
    )
    invalid_tags_result = IncomingTaskService(db_session).process_incoming_task(invalid_tags.id)
    assert invalid_tags_result.status == IncomingTaskStatus.REJECTED

    processed = IncomingTaskService(db_session).process_incoming_task(incoming.id)
    assert processed.status == IncomingTaskStatus.DUPLICATE


def test_incoming_task_service_edge_cases(db_session, monkeypatch):
    service = IncomingTaskService(db_session)
    task = service.create_task(
        IncomingTaskCreate(external_id="edge-1", raw_payload={"title": "Edge"}),
    )

    monkeypatch.setattr(service.repo, "update_status", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        service.board_repo,
        "get_default",
        lambda: type("Board", (), {"id": "board-1"})(),
    )
    monkeypatch.setattr(
        service.column_repo,
        "get_by_title",
        lambda *_args: type("Column", (), {"id": "column-1"})(),
    )
    monkeypatch.setattr(
        service.task_service,
        "create_task",
        lambda _payload: type(
            "Task",
            (),
            {
                "id": "task-1",
                "board_id": "board-1",
                "column_id": "column-1",
                "title": "Edge",
            },
        )(),
    )
    assert service.process_incoming_task(task.id) is None

    service = IncomingTaskService(db_session)
    task = service.create_task(
        IncomingTaskCreate(external_id="edge-2", raw_payload={"title": "Edge"}),
    )
    monkeypatch.setattr(service.board_repo, "get_default", lambda: None)
    with pytest.raises(ValueError):
        service.process_incoming_task(task.id)

    service = IncomingTaskService(db_session)
    task = service.create_task(
        IncomingTaskCreate(external_id="edge-3", raw_payload={"title": "Edge"}),
    )
    board = type("Board", (), {"id": "board-1"})()
    monkeypatch.setattr(service.board_repo, "get_default", lambda: board)
    monkeypatch.setattr(service.column_repo, "get_by_title", lambda *_args: None)
    with pytest.raises(ValueError):
        service.process_incoming_task(task.id)

    invalid_title = IncomingTaskService(db_session).create_task(
        IncomingTaskCreate(external_id="edge-4", raw_payload={}),
    )
    service = IncomingTaskService(db_session)
    monkeypatch.setattr(service.repo, "get_by_id", lambda _incoming_id: invalid_title)
    monkeypatch.setattr(service.repo, "update_status", lambda *args, **kwargs: None)
    assert service.process_incoming_task(invalid_title.id) is None

    invalid_tags = IncomingTaskService(db_session).create_task(
        IncomingTaskCreate(
            external_id="edge-5",
            raw_payload={"title": "Edge", "tags": [1]},
        )
    )
    service = IncomingTaskService(db_session)
    monkeypatch.setattr(service.repo, "get_by_id", lambda _incoming_id: invalid_tags)
    monkeypatch.setattr(service.repo, "update_status", lambda *args, **kwargs: None)
    assert service.process_incoming_task(invalid_tags.id) is None


def test_seed_demo_data_from_empty_database(db_session):
    seeded = seed_demo_data(db_session)
    assert seeded["board_created"] is True
    assert seeded["columns_created"] == 3
    assert seeded["tasks_created"] == 4
    assert seeded["rules_created"] == 4


def test_task_service_branch_cases(db_session, seeded_board, monkeypatch):
    service = TaskService(db_session)
    board = seeded_board["board"]
    todo = seeded_board["todo"]

    task = service.create_task(
        TaskCreate(
            board_id=board.id,
            column_id=todo.id,
            title="With position",
            position=9,
        )
    )
    assert service.list_tasks()[0].id == task.id

    monkeypatch.setattr(service.task_repo, "update", lambda *_args, **_kwargs: None)
    assert service.update_task(task.id, TaskUpdate(title="No persist", version=1)) is None
    assert service.move_task(task.id, TaskMove(column_id=todo.id, version=1)) is None

    monkeypatch.setattr(service.task_repo, "delete", lambda *_args, **_kwargs: False)
    assert service.delete_task(task.id) is False

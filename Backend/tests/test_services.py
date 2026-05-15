import pytest

from app.models.task import TaskPriority
from app.repositories.board_repository import BoardRepository, DEFAULT_BOARD_NAME
from app.repositories.column_repository import ColumnRepository
from app.schemas.column import ColumnCreate, ColumnUpdate
from app.schemas.task import TaskCreate, TaskMove, TaskUpdate
from app.services.board_service import BoardService
from app.services.column_service import ColumnHasTasksError, ColumnService
from app.services.task_service import TaskService, VersionConflictError, serialize_task


def test_board_service(db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    column_repo.create(board.id, "To Do", 1, True)

    service = BoardService(db_session)
    assert service.get_default_board() is not None
    assert service.get_board(board.id) is not None
    columns = service.list_columns(board.id)
    assert len(columns) == 1


def test_column_service_create_update_delete(db_session):
    board_repo = BoardRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)

    service = ColumnService(db_session)
    column = service.create_column(
        payload=ColumnCreate(board_id=board.id, title="Backlog", position=None, is_default=False)
    )
    assert column.position == 1

    column_explicit = service.create_column(
        payload=ColumnCreate(board_id=board.id, title="Doing", position=5, is_default=False)
    )
    assert column_explicit.position == 5

    updated = service.update_column(column.id, payload=ColumnUpdate())
    assert updated is not None

    with pytest.raises(ColumnHasTasksError):
        task_service = TaskService(db_session)
        task_service.create_task(
            payload=TaskCreate(
                board_id=board.id,
                column_id=column.id,
                title="Task",
                description=None,
                status="To Do",
                priority=TaskPriority.LOW,
                tags=[],
                deadline=None,
                position=1,
            )
        )
        service.delete_column(column.id)


def test_task_service_flow(db_session):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    column = column_repo.create(board.id, "To Do", 1, True)

    service = TaskService(db_session)
    task = service.create_task(
        payload=TaskCreate(
            board_id=board.id,
            column_id=column.id,
            title="Task",
            description=None,
            status=None,
            priority=TaskPriority.MEDIUM,
            tags=["tag"],
            deadline=None,
            position=None,
        )
    )

    all_tasks = service.list_tasks()
    assert len(all_tasks) == 1

    with pytest.raises(VersionConflictError):
        service.update_task(task.id, payload=TaskUpdate(version=0))

    same_task = service.update_task(task.id, payload=TaskUpdate(version=task.version))
    assert same_task is not None

    original_version = task.version
    updated = service.update_task(
        task.id,
        payload=TaskUpdate(title="Updated", version=original_version),
    )
    assert updated is not None
    assert updated.version == original_version + 1

    with pytest.raises(VersionConflictError):
        service.move_task(task.id, payload=TaskMove(column_id=column.id, version=0))

    with pytest.raises(ValueError):
        service.move_task(task.id, payload=TaskMove(column_id="missing", version=updated.version))

    moved = service.move_task(
        task.id,
        payload=TaskMove(
            column_id=column.id,
            status="To Do",
            position=2,
            version=updated.version,
        ),
    )
    assert moved is not None

    moved_default = service.move_task(
        task.id,
        payload=TaskMove(column_id=column.id, version=moved.version),
    )
    assert moved_default is not None
    assert moved_default.status == column.title

    assert service.delete_task(task.id) is True
    assert service.delete_task("missing") is False

    assert serialize_task(moved)["id"] == task.id


def test_task_service_create_invalid_column(db_session):
    board_repo = BoardRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    service = TaskService(db_session)

    with pytest.raises(ValueError):
        service.create_task(
            payload=TaskCreate(
                board_id=board.id,
                column_id="missing",
                title="Task",
                description=None,
                status=None,
                priority=TaskPriority.LOW,
                tags=[],
                deadline=None,
                position=None,
            )
        )

def test_task_service_concurrent_delete(db_session, monkeypatch):
    board_repo = BoardRepository(db_session)
    column_repo = ColumnRepository(db_session)
    board = board_repo.create(DEFAULT_BOARD_NAME)
    column = column_repo.create(board.id, "To Do", 1, True)

    service = TaskService(db_session)
    task = service.create_task(
        payload=TaskCreate(
            board_id=board.id,
            column_id=column.id,
            title="Task",
            priority=TaskPriority.LOW,
            tags=[]
        )
    )

    # Mock repo to return None/False for update/delete as if concurrently deleted
    monkeypatch.setattr(service.task_repo, "update", lambda *args, **kwargs: None)
    monkeypatch.setattr(service.task_repo, "delete", lambda *args, **kwargs: False)

    updated = service.update_task(task.id, payload=TaskUpdate(title="Updated", version=task.version))
    assert updated is None

    moved = service.move_task(task.id, payload=TaskMove(column_id=column.id, version=task.version))
    assert moved is None

    deleted = service.delete_task(task.id)
    assert deleted is False

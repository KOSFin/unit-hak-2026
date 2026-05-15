from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.rule_repository import AutomationRuleRepository
from app.repositories.task_repository import TaskRepository
from app.services.seed_service import seed_demo_data


def test_seed_demo_data_idempotent(db_session):
    result_first = seed_demo_data(db_session)
    result_second = seed_demo_data(db_session)

    board_repo = BoardRepository(db_session)
    board = board_repo.get_default()
    assert board is not None

    column_repo = ColumnRepository(db_session)
    columns = column_repo.list_by_board(board.id)
    assert {column.title for column in columns} == {"To Do", "In Progress", "Done"}

    task_repo = TaskRepository(db_session)
    tasks = task_repo.list_by_board(board.id)
    assert len(tasks) == 4

    rule_repo = AutomationRuleRepository(db_session)
    rules = rule_repo.list_all()
    assert len(rules) == 4

    assert result_first["tasks_created"] == 4
    assert result_second["tasks_created"] == 0
    assert result_second["columns_created"] == 0
    assert result_second["rules_created"] == 0

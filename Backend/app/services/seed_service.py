from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models.task import TaskPriority
from app.repositories.board_repository import DEFAULT_BOARD_NAME, BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.rule_repository import AutomationRuleRepository
from app.repositories.task_repository import TaskRepository

DEFAULT_COLUMNS = [
    {"title": "To Do", "position": 1, "is_default": True},
    {"title": "In Progress", "position": 2, "is_default": False},
    {"title": "Done", "position": 3, "is_default": False},
]

SEED_TASKS = [
    {
        "title": "Draft project brief",
        "description": "Write a short summary of the project scope",
        "priority": TaskPriority.MEDIUM,
        "tags": ["planning"],
        "deadline_offset_hours": None,
    },
    {
        "title": "Urgent: validate flow",
        "description": "Check urgent automation path",
        "priority": TaskPriority.MEDIUM,
        "tags": ["urgent"],
        "deadline_offset_hours": None,
    },
    {
        "title": "Review with deadline",
        "description": "Demo task with deadline",
        "priority": TaskPriority.MEDIUM,
        "tags": [],
        "deadline_offset_hours": 12,
    },

]

SEED_RULES = [
    {
        "name": "Urgent tag escalates priority",
        "enabled": True,
        "trigger_type": "TASK_ANY",
        "condition": {"tag": "urgent"},
        "action": {
            "set_priority": "HIGH",
            "notify": "Priority set to HIGH because tag 'urgent' is present",
        },
    },

    {
        "name": "Deadline soon flag",
        "enabled": True,
        "trigger_type": "TASK_ANY",
        "condition": {"deadline_hours_lt": 24, "not_tag": "deadline-soon"},
        "action": {"add_tag": "deadline-soon", "notify": "Deadline within 24 hours"},
    },
    {
        "name": "Done notification",
        "enabled": True,
        "trigger_type": "TASK_MOVED",
        "condition": {"column": "Done"},
        "action": {"notify": "Task completed"},
    },
]


def seed_demo_data(session) -> dict[str, int | bool]:
    board_repo = BoardRepository(session)
    column_repo = ColumnRepository(session)
    task_repo = TaskRepository(session)
    rule_repo = AutomationRuleRepository(session)

    board = board_repo.get_default()
    board_created = False
    if not board:
        board = board_repo.create(DEFAULT_BOARD_NAME)
        board_created = True

    columns = {column.title: column for column in column_repo.list_by_board(board.id)}
    columns_created = 0
    for column in DEFAULT_COLUMNS:
        if column["title"] in columns:
            continue
        column_repo.create(board.id, column["title"], column["position"], column["is_default"])
        columns_created += 1

    columns = {column.title: column for column in column_repo.list_by_board(board.id)}
    tasks_created = 0
    if not task_repo.list_by_board(board.id):
        now = datetime.now(UTC)
        for index, seed_task in enumerate(SEED_TASKS, start=1):
            deadline = None
            if seed_task["deadline_offset_hours"] is not None:
                deadline = now + timedelta(hours=seed_task["deadline_offset_hours"])
            task_repo.create(
                board_id=board.id,
                column_id=columns["To Do"].id,
                title=seed_task["title"],
                description=seed_task["description"],
                status="To Do",
                priority=seed_task["priority"],
                tags=list(seed_task["tags"]),
                deadline=deadline,
                position=index,
            )
            tasks_created += 1

    rules_created = 0
    if not rule_repo.list_all():
        for rule in SEED_RULES:
            rule_repo.create(
                name=rule["name"],
                enabled=rule["enabled"],
                trigger_type=rule["trigger_type"],
                condition=rule["condition"],
                action=rule["action"],
            )
            rules_created += 1

    return {
        "board_created": board_created,
        "columns_created": columns_created,
        "tasks_created": tasks_created,
        "rules_created": rules_created,
    }

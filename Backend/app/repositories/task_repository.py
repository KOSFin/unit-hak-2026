from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        board_id: str,
        column_id: str,
        title: str,
        description: str | None,
        status: str,
        priority: TaskPriority,
        tags: list[str],
        deadline,
        position: int,
        version: int = 1,
    ) -> Task:
        task = Task(
            board_id=board_id,
            column_id=column_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            tags=tags,
            deadline=deadline,
            position=position,
            version=version,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_by_id(self, task_id: str) -> Task | None:
        return self.session.get(Task, task_id)

    def list_by_board(self, board_id: str) -> list[Task]:
        stmt = select(Task).where(Task.board_id == board_id).order_by(Task.position)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_column(self, column_id: str) -> list[Task]:
        stmt = select(Task).where(Task.column_id == column_id).order_by(Task.position)
        return list(self.session.execute(stmt).scalars().all())

    def list_all(self) -> list[Task]:
        stmt = select(Task).order_by(Task.position)
        return list(self.session.execute(stmt).scalars().all())

    def get_max_position(self, board_id: str, column_id: str) -> int:
        stmt = select(func.max(Task.position)).where(
            Task.board_id == board_id,
            Task.column_id == column_id,
        )
        result = self.session.execute(stmt).scalar_one()
        return int(result or 0)

    def count_by_column(self, column_id: str) -> int:
        stmt = select(func.count()).where(Task.column_id == column_id)
        return int(self.session.execute(stmt).scalar_one())

    def reorder_positions(self, column_id: str) -> None:
        """Renumber all tasks in a column so positions are contiguous 1-based integers."""
        tasks = self.list_by_column(column_id)
        for idx, task in enumerate(tasks, start=1):
            if task.position != idx:
                task.position = idx
        self.session.commit()

    def update(self, task_id: str, **changes) -> Task | None:
        task = self.get_by_id(task_id)
        if not task:
            return None
        for field, value in changes.items():
            setattr(task, field, value)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete(self, task_id: str) -> bool:
        task = self.get_by_id(task_id)
        if not task:
            return False
        self.session.delete(task)
        self.session.commit()
        return True

from sqlalchemy import select
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

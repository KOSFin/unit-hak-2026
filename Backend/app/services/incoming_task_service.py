from sqlalchemy.orm import Session

from app.models.incoming_task import IncomingTaskStatus
from app.repositories.incoming_task_repository import IncomingTaskRepository


class IncomingTaskService:
    def __init__(self, session: Session):
        self.repo = IncomingTaskRepository(session)

    def list_tasks(self, skip: int = 0, limit: int = 50, status: str | None = None):
        tasks = self.repo.list_all()
        if status:
            tasks = [t for t in tasks if t.status.value == status]
        return tasks[skip:skip+limit]

    def update_status(self, task_id: str, status: str):
        task = self.repo.get_by_id(task_id)
        if not task:
            return None
        enum_status = IncomingTaskStatus(status)
        return self.repo.update_status(task_id, enum_status)

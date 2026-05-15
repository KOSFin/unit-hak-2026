from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.column import Column


class ColumnRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, board_id: str, title: str, position: int, is_default: bool) -> Column:
        column = Column(
            board_id=board_id,
            title=title,
            position=position,
            is_default=is_default,
        )
        self.session.add(column)
        self.session.commit()
        self.session.refresh(column)
        return column

    def get_by_id(self, column_id: str) -> Column | None:
        return self.session.get(Column, column_id)

    def list_by_board(self, board_id: str) -> list[Column]:
        stmt = select(Column).where(Column.board_id == board_id).order_by(Column.position)
        return list(self.session.execute(stmt).scalars().all())

    def update(self, column_id: str, **changes) -> Column | None:
        column = self.get_by_id(column_id)
        if not column:
            return None
        for field, value in changes.items():
            setattr(column, field, value)
        self.session.commit()
        self.session.refresh(column)
        return column

    def delete(self, column_id: str) -> bool:
        column = self.get_by_id(column_id)
        if not column:
            return False
        self.session.delete(column)
        self.session.commit()
        return True

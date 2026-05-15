from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DomainEventSchema(BaseModel):
    id: str
    type: str
    entity_type: str
    entity_id: str | None = None
    payload: dict[str, Any]
    processed: bool | None = None
    error: str | None = None
    created_at: datetime
    processed_at: datetime | None = None

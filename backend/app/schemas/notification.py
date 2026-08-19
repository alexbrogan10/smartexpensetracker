import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool
    related_transaction_id: uuid.UUID | None
    created_at: datetime


class UnreadCountRead(BaseModel):
    count: int


class MarkAllReadResult(BaseModel):
    marked_read: int

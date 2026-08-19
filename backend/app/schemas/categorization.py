import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import TransactionType


class CategorySuggestionRequest(BaseModel):
    type: TransactionType
    payee: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)


class CategorySuggestion(BaseModel):
    category_id: uuid.UUID
    category_name: str
    confidence: float


class CategorySuggestionResponse(BaseModel):
    status: Literal["ok", "insufficient_data"]
    suggestions: list[CategorySuggestion]

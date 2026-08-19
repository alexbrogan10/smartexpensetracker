import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class CategoryPrediction(BaseModel):
    category_id: uuid.UUID
    category_name: str
    predicted_amount: Decimal


class SpendingPredictionResponse(BaseModel):
    status: Literal["ok", "insufficient_data"]
    next_month: str
    predicted_income: Decimal | None
    predicted_expenses: Decimal | None
    by_category: list[CategoryPrediction]

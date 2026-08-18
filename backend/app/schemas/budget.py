import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.category import CategoryRead

BudgetStatus = Literal["ok", "warning", "exceeded"]

# A budget is "warning" once spending crosses this fraction of its limit, and
# "exceeded" at or beyond the limit itself.
WARNING_THRESHOLD = Decimal("0.8")


def compute_status(spent: Decimal, limit: Decimal | None) -> BudgetStatus:
    if limit is None or limit == 0:
        return "ok"
    ratio = spent / limit
    if ratio >= 1:
        return "exceeded"
    if ratio >= WARNING_THRESHOLD:
        return "warning"
    return "ok"


class BudgetCategoryInput(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class BudgetCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)
    overall_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category_limits: list[BudgetCategoryInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def _no_duplicate_categories(self) -> "BudgetCreate":
        category_ids = [c.category_id for c in self.category_limits]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("category_limits cannot repeat the same category")
        return self


class BudgetUpdate(BaseModel):
    overall_amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category_limits: list[BudgetCategoryInput] | None = None

    @model_validator(mode="after")
    def _no_duplicate_categories(self) -> "BudgetUpdate":
        if self.category_limits is None:
            return self
        category_ids = [c.category_id for c in self.category_limits]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("category_limits cannot repeat the same category")
        return self


class BudgetCategoryRead(BaseModel):
    id: uuid.UUID
    category: CategoryRead
    amount: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: float
    status: BudgetStatus


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    month: int
    year: int
    overall_amount: Decimal | None
    overall_spent: Decimal
    overall_remaining: Decimal | None
    overall_percent_used: float | None
    overall_status: BudgetStatus
    category_limits: list[BudgetCategoryRead]
    created_at: datetime
    updated_at: datetime

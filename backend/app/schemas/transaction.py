import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import PaymentMethod, RecurringFrequency, TransactionType
from app.schemas.category import CategoryRead


class TransactionCreate(BaseModel):
    type: TransactionType
    category_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payee: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    transaction_date: date
    payment_method: PaymentMethod | None = None
    is_recurring: bool = False
    recurring_frequency: RecurringFrequency | None = None

    @model_validator(mode="after")
    def _check_recurring_frequency(self) -> "TransactionCreate":
        if self.is_recurring and self.recurring_frequency is None:
            raise ValueError("recurring_frequency is required when is_recurring is true")
        if not self.is_recurring and self.recurring_frequency is not None:
            raise ValueError("recurring_frequency must be omitted when is_recurring is false")
        return self


class TransactionUpdate(BaseModel):
    """Partial update: only provided fields are changed."""

    type: TransactionType | None = None
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    payee: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    transaction_date: date | None = None
    payment_method: PaymentMethod | None = None
    is_recurring: bool | None = None
    recurring_frequency: RecurringFrequency | None = None

    @model_validator(mode="after")
    def _check_recurring_frequency(self) -> "TransactionUpdate":
        if self.is_recurring is True and self.recurring_frequency is None:
            raise ValueError("recurring_frequency is required when is_recurring is true")
        if self.is_recurring is False and self.recurring_frequency is not None:
            raise ValueError("recurring_frequency must be omitted when is_recurring is false")
        return self


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: TransactionType
    category: CategoryRead
    amount: Decimal
    payee: str
    description: str | None
    transaction_date: date
    payment_method: PaymentMethod | None
    is_recurring: bool
    recurring_frequency: RecurringFrequency | None
    created_at: datetime
    updated_at: datetime

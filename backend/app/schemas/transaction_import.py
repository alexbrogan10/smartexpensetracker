import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportStatus, PaymentMethod, RecurringFrequency, TransactionType

RowStatus = Literal["valid", "error", "duplicate"]


class ParsedTransactionFields(BaseModel):
    type: TransactionType
    category_id: uuid.UUID
    category_name: str
    amount: Decimal
    payee: str
    description: str | None
    transaction_date: date
    payment_method: PaymentMethod | None
    is_recurring: bool
    recurring_frequency: RecurringFrequency | None


class ImportRowPreview(BaseModel):
    row_number: int
    raw: dict[str, str]
    status: RowStatus
    errors: list[str]
    fields: ParsedTransactionFields | None


class ImportPreviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: ImportStatus
    total_rows: int
    valid_rows: int
    error_rows: int
    duplicate_rows: int
    rows: list[ImportRowPreview]
    created_at: datetime


class ImportConfirmRequest(BaseModel):
    include_duplicates: bool = False


class ImportConfirmResult(BaseModel):
    imported_count: int
    skipped_count: int

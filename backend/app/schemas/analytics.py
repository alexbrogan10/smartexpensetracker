import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import RecurringFrequency, TransactionType
from app.schemas.category import CategoryRead


class SummaryRead(BaseModel):
    month: int
    year: int
    income: Decimal
    expenses: Decimal
    net_cash_flow: Decimal
    previous_month_income: Decimal
    previous_month_expenses: Decimal
    income_change_percent: float | None
    expenses_change_percent: float | None


class CategoryBreakdownItem(BaseModel):
    category: CategoryRead
    amount: Decimal
    transaction_count: int
    percent_of_total: float


class TrendItem(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    net_cash_flow: Decimal


class MerchantItem(BaseModel):
    payee: str
    total_amount: Decimal
    transaction_count: int


class RecurringSeriesItem(BaseModel):
    payee: str
    category: CategoryRead
    type: TransactionType
    amount: Decimal
    frequency: RecurringFrequency
    last_date: date
    next_due_date: date
    transaction_id: uuid.UUID


class RecurringAnalysisRead(BaseModel):
    series: list[RecurringSeriesItem]
    total_monthly_estimate: Decimal

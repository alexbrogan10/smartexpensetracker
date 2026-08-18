import calendar
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import PaymentMethod, TransactionType
from app.models.transaction import Transaction

SortField = Literal["transaction_date", "amount"]
SortOrder = Literal["asc", "desc"]


@dataclass(kw_only=True)
class TransactionFilters:
    type: TransactionType | None = None
    category_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    is_recurring: bool | None = None
    payment_method: PaymentMethod | None = None
    search: str | None = None
    sort_by: SortField = "transaction_date"
    sort_order: SortOrder = "desc"
    page: int = 1
    page_size: int = 25


def _apply_filters(stmt, user_id: uuid.UUID, filters: TransactionFilters):
    stmt = stmt.where(Transaction.user_id == user_id)

    if filters.type is not None:
        stmt = stmt.where(Transaction.type == filters.type)
    if filters.category_id is not None:
        stmt = stmt.where(Transaction.category_id == filters.category_id)
    if filters.date_from is not None:
        stmt = stmt.where(Transaction.transaction_date >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(Transaction.transaction_date <= filters.date_to)
    if filters.min_amount is not None:
        stmt = stmt.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        stmt = stmt.where(Transaction.amount <= filters.max_amount)
    if filters.is_recurring is not None:
        stmt = stmt.where(Transaction.is_recurring == filters.is_recurring)
    if filters.payment_method is not None:
        stmt = stmt.where(Transaction.payment_method == filters.payment_method)
    if filters.search:
        pattern = f"%{filters.search}%"
        stmt = stmt.where(
            or_(Transaction.payee.ilike(pattern), Transaction.description.ilike(pattern))
        )

    return stmt


def list_transactions(
    db: Session, user_id: uuid.UUID, filters: TransactionFilters
) -> tuple[list[Transaction], int]:
    """Return (page of transactions, total matching count) for the given filters."""
    base_stmt = _apply_filters(select(Transaction), user_id, filters)

    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    sort_columns: dict[SortField, object] = {
        "transaction_date": Transaction.transaction_date,
        "amount": Transaction.amount,
    }
    sort_column = sort_columns[filters.sort_by]
    order_by = sort_column.asc() if filters.sort_order == "asc" else sort_column.desc()

    items_stmt = (
        base_stmt.options(joinedload(Transaction.category))
        .order_by(order_by, Transaction.id)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    )
    items = list(db.scalars(items_stmt).unique().all())

    return items, total


def get_transaction_for_user(
    db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction | None:
    stmt = (
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
    )
    return db.scalar(stmt)


def _month_date_range(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def get_expense_totals_by_category(
    db: Session, user_id: uuid.UUID, year: int, month: int
) -> dict[uuid.UUID, Decimal]:
    """Sum of expense transactions per category for one calendar month.

    Used by budget progress calculations; reused as-is by month-over-month
    analytics once that milestone lands, so it lives here rather than in a
    budget-specific module.
    """
    date_from, date_to = _month_date_range(year, month)
    stmt = (
        select(Transaction.category_id, func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(Transaction.category_id)
    )
    return dict(db.execute(stmt).all())


def get_total_expenses(db: Session, user_id: uuid.UUID, year: int, month: int) -> Decimal:
    date_from, date_to = _month_date_range(year, month)
    stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == TransactionType.EXPENSE,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    )
    total = db.scalar(stmt)
    return total if total is not None else Decimal("0")

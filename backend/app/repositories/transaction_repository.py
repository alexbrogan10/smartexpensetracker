import calendar
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
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


def month_date_range(year: int, month: int) -> tuple[date, date]:
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
    date_from, date_to = month_date_range(year, month)
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


def _get_total_by_type(
    db: Session, user_id: uuid.UUID, year: int, month: int, type_: TransactionType
) -> Decimal:
    date_from, date_to = month_date_range(year, month)
    stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == type_,
        Transaction.transaction_date >= date_from,
        Transaction.transaction_date <= date_to,
    )
    total = db.scalar(stmt)
    return total if total is not None else Decimal("0")


def get_total_expenses(db: Session, user_id: uuid.UUID, year: int, month: int) -> Decimal:
    return _get_total_by_type(db, user_id, year, month, TransactionType.EXPENSE)


def get_total_income(db: Session, user_id: uuid.UUID, year: int, month: int) -> Decimal:
    return _get_total_by_type(db, user_id, year, month, TransactionType.INCOME)


def get_category_breakdown(
    db: Session, user_id: uuid.UUID, year: int, month: int, type_: TransactionType
) -> list[tuple[Category, Decimal, int]]:
    """Per-category totals (with transaction count) for one calendar month."""
    date_from, date_to = month_date_range(year, month)
    stmt = (
        select(Category, func.sum(Transaction.amount), func.count(Transaction.id))
        .join(Transaction, Transaction.category_id == Category.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.type == type_,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
    )
    return list(db.execute(stmt).all())


def get_top_merchants(
    db: Session, user_id: uuid.UUID, date_from: date, date_to: date, limit: int
) -> list[tuple[str, Decimal, int]]:
    """Top expense payees by total spend within a date range."""
    stmt = (
        select(Transaction.payee, func.sum(Transaction.amount), func.count(Transaction.id))
        .where(
            Transaction.user_id == user_id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(Transaction.payee)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )
    return list(db.execute(stmt).all())


def get_recurring_transactions(db: Session, user_id: uuid.UUID) -> list[Transaction]:
    """All transactions flagged recurring, most recent first.

    Callers group these by payee to find each series' most recent
    occurrence, since there's no dedicated recurring-series table yet.
    """
    stmt = (
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.user_id == user_id, Transaction.is_recurring.is_(True))
        .order_by(Transaction.transaction_date.desc())
    )
    return list(db.scalars(stmt).unique().all())


def transaction_exists(
    db: Session, user_id: uuid.UUID, transaction_date: date, payee: str, amount: Decimal
) -> bool:
    """Whether a transaction with this date/payee/amount already exists.

    Used for import duplicate detection: date + amount + case-insensitive
    payee is a reasonable heuristic, not a guarantee (it can't distinguish
    two genuinely separate purchases of the same amount, from the same
    merchant, on the same day).
    """
    stmt = (
        select(Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_date == transaction_date,
            Transaction.amount == amount,
            func.lower(Transaction.payee) == payee.lower(),
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


MAX_EXPORT_ROWS = 10_000


def list_categorized_texts(
    db: Session, user_id: uuid.UUID, type_: TransactionType
) -> list[tuple[str, str | None, uuid.UUID]]:
    """(payee, description, category_id) for all of a user's transactions of one type.

    Training data for per-user category suggestion — every existing
    transaction is already a confirmed (text -> category) example.
    """
    stmt = select(Transaction.payee, Transaction.description, Transaction.category_id).where(
        Transaction.user_id == user_id, Transaction.type == type_
    )
    return list(db.execute(stmt).all())


def list_transactions_for_export(
    db: Session, user_id: uuid.UUID, filters: TransactionFilters
) -> list[Transaction]:
    """All transactions matching `filters`, unpaginated (capped at MAX_EXPORT_ROWS)."""
    stmt = (
        _apply_filters(select(Transaction), user_id, filters)
        .options(joinedload(Transaction.category))
        .order_by(Transaction.transaction_date.desc(), Transaction.id)
        .limit(MAX_EXPORT_ROWS)
    )
    return list(db.scalars(stmt).unique().all())

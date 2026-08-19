import calendar
import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import RecurringFrequency, TransactionType
from app.models.transaction import Transaction
from app.repositories import transaction_repository
from app.schemas.analytics import (
    CategoryBreakdownItem,
    MerchantItem,
    RecurringAnalysisRead,
    RecurringSeriesItem,
    SummaryRead,
    TrendItem,
)
from app.schemas.category import CategoryRead

# Approximate how many times a recurring series lands per month, used to
# normalize "$X every N weeks/months" into a single comparable monthly figure.
_MONTHLY_FACTOR: dict[RecurringFrequency, Decimal] = {
    RecurringFrequency.WEEKLY: Decimal(52) / Decimal(12),
    RecurringFrequency.BIWEEKLY: Decimal(26) / Decimal(12),
    RecurringFrequency.MONTHLY: Decimal(1),
    RecurringFrequency.QUARTERLY: Decimal(1) / Decimal(3),
    RecurringFrequency.YEARLY: Decimal(1) / Decimal(12),
}


def add_months(d: date, months: int) -> date:
    """Add (or subtract) whole calendar months, clamping the day to the
    target month's length (e.g. Jan 31 + 1 month -> Feb 28)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def compute_next_due_date(last_date: date, frequency: RecurringFrequency) -> date:
    if frequency == RecurringFrequency.WEEKLY:
        return last_date + timedelta(days=7)
    if frequency == RecurringFrequency.BIWEEKLY:
        return last_date + timedelta(days=14)
    if frequency == RecurringFrequency.MONTHLY:
        return add_months(last_date, 1)
    if frequency == RecurringFrequency.QUARTERLY:
        return add_months(last_date, 3)
    return add_months(last_date, 12)  # yearly


def _percent_change(previous: Decimal, current: Decimal) -> float | None:
    if previous == 0:
        return None
    return float((current - previous) / previous * 100)


def get_summary(db: Session, user_id: uuid.UUID, year: int, month: int) -> SummaryRead:
    income = transaction_repository.get_total_income(db, user_id, year, month)
    expenses = transaction_repository.get_total_expenses(db, user_id, year, month)

    previous = add_months(date(year, month, 1), -1)
    previous_income = transaction_repository.get_total_income(
        db, user_id, previous.year, previous.month
    )
    previous_expenses = transaction_repository.get_total_expenses(
        db, user_id, previous.year, previous.month
    )

    return SummaryRead(
        month=month,
        year=year,
        income=income,
        expenses=expenses,
        net_cash_flow=income - expenses,
        previous_month_income=previous_income,
        previous_month_expenses=previous_expenses,
        income_change_percent=_percent_change(previous_income, income),
        expenses_change_percent=_percent_change(previous_expenses, expenses),
    )


def get_category_breakdown(
    db: Session, user_id: uuid.UUID, year: int, month: int, type_: TransactionType
) -> list[CategoryBreakdownItem]:
    rows = transaction_repository.get_category_breakdown(db, user_id, year, month, type_)
    total = sum((amount for _, amount, _ in rows), Decimal("0"))

    return [
        CategoryBreakdownItem(
            category=CategoryRead.model_validate(category),
            amount=amount,
            transaction_count=count,
            percent_of_total=round(float(amount / total * 100), 1) if total else 0.0,
        )
        for category, amount, count in rows
    ]


def get_trends(db: Session, user_id: uuid.UUID, months: int) -> list[TrendItem]:
    """Oldest-to-newest monthly income/expense/net totals for the last `months` months."""
    today = date.today()
    current_month_start = date(today.year, today.month, 1)

    items = []
    for offset in range(months - 1, -1, -1):
        month_date = add_months(current_month_start, -offset)
        income = transaction_repository.get_total_income(
            db, user_id, month_date.year, month_date.month
        )
        expenses = transaction_repository.get_total_expenses(
            db, user_id, month_date.year, month_date.month
        )
        items.append(
            TrendItem(
                year=month_date.year,
                month=month_date.month,
                income=income,
                expenses=expenses,
                net_cash_flow=income - expenses,
            )
        )
    return items


def get_top_merchants(
    db: Session, user_id: uuid.UUID, year: int, month: int, limit: int
) -> list[MerchantItem]:
    date_from, date_to = transaction_repository.month_date_range(year, month)
    rows = transaction_repository.get_top_merchants(db, user_id, date_from, date_to, limit)
    return [
        MerchantItem(payee=payee, total_amount=amount, transaction_count=count)
        for payee, amount, count in rows
    ]


def get_recurring_analysis(db: Session, user_id: uuid.UUID) -> RecurringAnalysisRead:
    all_recurring = transaction_repository.get_recurring_transactions(db, user_id)

    # get_recurring_transactions is already ordered most-recent-first, so the
    # first transaction seen per payee is that series' latest occurrence.
    latest_by_payee: dict[str, Transaction] = {}
    for txn in all_recurring:
        latest_by_payee.setdefault(txn.payee, txn)

    series: list[RecurringSeriesItem] = []
    total_monthly_estimate = Decimal("0")
    for txn in latest_by_payee.values():
        frequency = txn.recurring_frequency
        assert frequency is not None  # guaranteed by the is_recurring DB constraint

        series.append(
            RecurringSeriesItem(
                payee=txn.payee,
                category=CategoryRead.model_validate(txn.category),
                type=txn.type,
                amount=txn.amount,
                frequency=frequency,
                last_date=txn.transaction_date,
                next_due_date=compute_next_due_date(txn.transaction_date, frequency),
                transaction_id=txn.id,
            )
        )
        if txn.type == TransactionType.EXPENSE:
            total_monthly_estimate += txn.amount * _MONTHLY_FACTOR[frequency]

    series.sort(key=lambda item: item.next_due_date)

    return RecurringAnalysisRead(
        series=series,
        total_monthly_estimate=total_monthly_estimate.quantize(Decimal("0.01")),
    )

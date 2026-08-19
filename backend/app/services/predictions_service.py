import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.prediction import forecast_next, has_enough_data
from app.models.category import Category
from app.repositories import transaction_repository
from app.schemas.analytics import TrendItem
from app.schemas.prediction import CategoryPrediction, SpendingPredictionResponse
from app.services.analytics_service import add_months, get_trends

# How many complete past months to train the trend on.
LOOKBACK_MONTHS = 6
MAX_CATEGORY_PREDICTIONS = 5

# Forecasting the next full calendar month, not the in-progress current one:
# the training window ends at "last complete month" (one month before today),
# so that target is two steps past the window's last point.
_STEPS_TO_NEXT_MONTH = 2


def get_spending_prediction(db: Session, user_id: uuid.UUID) -> SpendingPredictionResponse:
    today = date.today()
    current_month_start = date(today.year, today.month, 1)
    next_month = add_months(current_month_start, 1)
    next_month_label = f"{next_month.year:04d}-{next_month.month:02d}"

    trend = get_trends(db, user_id, LOOKBACK_MONTHS + 1)
    complete_months = trend[:-1]  # drop the current, still in-progress month

    expense_values = [m.expenses for m in complete_months]
    income_values = [m.income for m in complete_months]

    if not has_enough_data(expense_values) and not has_enough_data(income_values):
        return SpendingPredictionResponse(
            status="insufficient_data",
            next_month=next_month_label,
            predicted_income=None,
            predicted_expenses=None,
            by_category=[],
        )

    predicted_income = (
        forecast_next(income_values, steps_ahead=_STEPS_TO_NEXT_MONTH)
        if has_enough_data(income_values)
        else None
    )
    predicted_expenses = (
        forecast_next(expense_values, steps_ahead=_STEPS_TO_NEXT_MONTH)
        if has_enough_data(expense_values)
        else None
    )

    return SpendingPredictionResponse(
        status="ok",
        next_month=next_month_label,
        predicted_income=predicted_income,
        predicted_expenses=predicted_expenses,
        by_category=_predict_categories(db, user_id, complete_months),
    )


def _predict_categories(
    db: Session, user_id: uuid.UUID, complete_months: list[TrendItem]
) -> list[CategoryPrediction]:
    per_month_totals = [
        transaction_repository.get_expense_totals_by_category(db, user_id, item.year, item.month)
        for item in complete_months
    ]
    all_category_ids: set[uuid.UUID] = set()
    for totals in per_month_totals:
        all_category_ids.update(totals.keys())

    candidates: list[tuple[uuid.UUID, Decimal]] = []
    for category_id in all_category_ids:
        values = [totals.get(category_id, Decimal("0")) for totals in per_month_totals]
        if not has_enough_data(values):
            continue
        predicted = forecast_next(values, steps_ahead=_STEPS_TO_NEXT_MONTH)
        if predicted > 0:
            candidates.append((category_id, predicted))

    candidates.sort(key=lambda c: c[1], reverse=True)
    top = candidates[:MAX_CATEGORY_PREDICTIONS]
    if not top:
        return []

    stmt = select(Category).where(Category.id.in_([c[0] for c in top]))
    categories = {c.id: c for c in db.scalars(stmt).all()}

    return [
        CategoryPrediction(
            category_id=category_id,
            category_name=categories[category_id].name,
            predicted_amount=predicted,
        )
        for category_id, predicted in top
        if category_id in categories
    ]

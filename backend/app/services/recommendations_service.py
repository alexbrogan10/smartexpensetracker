import calendar
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories import transaction_repository
from app.schemas.budget import BudgetRead
from app.schemas.recommendation import Recommendation, RecommendationsResponse
from app.services import budget_service, savings_goal_service
from app.services.analytics_service import add_months

# A category's prior-month spend must clear this floor before a trend
# recommendation fires at all, so a brand new $3/month category can't look
# like a 500% spike.
TREND_MIN_PREVIOUS_AMOUNT = Decimal("20")
TREND_MIN_INCREASE_PERCENT = Decimal("0.2")
TREND_MIN_INCREASE_AMOUNT = Decimal("20")
MAX_TREND_RECOMMENDATIONS = 3


def _elapsed_fraction(today: date) -> Decimal:
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    return Decimal(today.day) / Decimal(days_in_month)


def _budget_recommendations(budget: BudgetRead, fraction: Decimal) -> list[Recommendation]:
    out: list[Recommendation] = []

    if budget.overall_amount:
        if budget.overall_status == "exceeded":
            over = budget.overall_spent - budget.overall_amount
            out.append(
                Recommendation(
                    type="budget_pace",
                    severity="critical",
                    message=f"You've exceeded your overall budget by ${over:.2f} this month.",
                )
            )
        else:
            projected = (budget.overall_spent / fraction).quantize(Decimal("0.01"))
            if projected > budget.overall_amount:
                over = (projected - budget.overall_amount).quantize(Decimal("0.01"))
                out.append(
                    Recommendation(
                        type="budget_pace",
                        severity="warning",
                        message=(
                            "At this pace, you're on track to exceed your overall "
                            f"budget by about ${over:.2f} this month."
                        ),
                    )
                )

    for limit in budget.category_limits:
        if limit.status == "exceeded":
            over = limit.spent - limit.amount
            out.append(
                Recommendation(
                    type="budget_pace",
                    severity="critical",
                    category_id=limit.category.id,
                    message=(
                        f"You've exceeded your {limit.category.name} budget "
                        f"by ${over:.2f} this month."
                    ),
                )
            )
        else:
            projected = (limit.spent / fraction).quantize(Decimal("0.01"))
            if projected > limit.amount:
                over = (projected - limit.amount).quantize(Decimal("0.01"))
                out.append(
                    Recommendation(
                        type="budget_pace",
                        severity="warning",
                        category_id=limit.category.id,
                        message=(
                            "At this pace, you're on track to exceed your "
                            f"{limit.category.name} budget by about ${over:.2f} this month."
                        ),
                    )
                )

    return out


def _category_trend_recommendations(
    db: Session, user_id: uuid.UUID, today: date, fraction: Decimal
) -> list[Recommendation]:
    current_totals = transaction_repository.get_expense_totals_by_category(
        db, user_id, today.year, today.month
    )
    previous_month = add_months(date(today.year, today.month, 1), -1)
    previous_totals = transaction_repository.get_expense_totals_by_category(
        db, user_id, previous_month.year, previous_month.month
    )

    candidates: list[tuple[uuid.UUID, Decimal, Decimal, Decimal]] = []
    for category_id, current_amount in current_totals.items():
        previous_amount = previous_totals.get(category_id, Decimal("0"))
        if previous_amount < TREND_MIN_PREVIOUS_AMOUNT:
            continue

        projected = (current_amount / fraction).quantize(Decimal("0.01"))
        increase = projected - previous_amount
        if increase < TREND_MIN_INCREASE_AMOUNT:
            continue
        if increase / previous_amount < TREND_MIN_INCREASE_PERCENT:
            continue

        candidates.append((category_id, previous_amount, projected, increase))

    candidates.sort(key=lambda c: c[3], reverse=True)
    top = candidates[:MAX_TREND_RECOMMENDATIONS]
    if not top:
        return []

    stmt = select(Category).where(Category.id.in_([c[0] for c in top]))
    categories = {c.id: c for c in db.scalars(stmt).all()}

    out: list[Recommendation] = []
    for category_id, previous_amount, projected, increase in top:
        category = categories.get(category_id)
        if category is None:
            continue
        percent = (increase / previous_amount * 100).quantize(Decimal("1"))
        out.append(
            Recommendation(
                type="category_trend",
                severity="info",
                category_id=category_id,
                message=(
                    f"Your {category.name} spending is on pace to be about {percent}% "
                    f"higher than last month (${projected:.2f} vs ${previous_amount:.2f})."
                ),
            )
        )
    return out


def get_recommendations(db: Session, user_id: uuid.UUID) -> RecommendationsResponse:
    today = date.today()
    fraction = _elapsed_fraction(today)

    recommendations: list[Recommendation] = []

    budget = budget_service.get_current_budget(db, user_id)
    if budget is not None:
        recommendations.extend(_budget_recommendations(budget, fraction))

    recommendations.extend(_category_trend_recommendations(db, user_id, today, fraction))

    for goal in savings_goal_service.list_savings_goals(db, user_id):
        if goal.target_date is not None and goal.is_on_track is False:
            recommendations.append(
                Recommendation(
                    type="savings_off_track",
                    severity="warning",
                    goal_id=goal.id,
                    message=(
                        f'Your "{goal.name}" savings goal is behind pace to reach '
                        f"${goal.target_amount:.2f} by {goal.target_date.isoformat()}."
                    ),
                )
            )

    return RecommendationsResponse(recommendations=recommendations)

"""Direct unit tests for the pace-projection helpers in recommendations_service.

These bypass the API (and therefore real wall-clock dates) by constructing
BudgetRead/CategoryRead objects and passing an explicit `fraction` directly.
The "pace" recommendations only fire depending on how far into the month
`today` is, which made them impractical to test deterministically through
the API - unit-testing the private helpers with a controlled fraction closes
that gap without any date dependence at all.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from app.schemas.budget import BudgetCategoryRead, BudgetRead
from app.schemas.category import CategoryRead
from app.services.recommendations_service import (
    _budget_recommendations,
    _category_trend_recommendations,
)
from tests.helpers import get_category_id, register_and_login

NOW = datetime(2026, 8, 1)


def make_category(name: str = "Groceries") -> CategoryRead:
    return CategoryRead(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name=name,
        type="expense",
        icon=None,
        color=None,
        is_default=False,
        created_at=NOW,
        updated_at=NOW,
    )


def make_budget(
    overall_amount: str | None,
    overall_spent: str,
    overall_status: str,
    category_limits: list[BudgetCategoryRead] | None = None,
) -> BudgetRead:
    return BudgetRead(
        id=uuid.uuid4(),
        month=8,
        year=2026,
        overall_amount=Decimal(overall_amount) if overall_amount else None,
        overall_spent=Decimal(overall_spent),
        overall_remaining=None,
        overall_percent_used=None,
        overall_status=overall_status,
        category_limits=category_limits or [],
        created_at=NOW,
        updated_at=NOW,
    )


def make_limit(amount: str, spent: str, status: str) -> BudgetCategoryRead:
    return BudgetCategoryRead(
        id=uuid.uuid4(),
        category=make_category(),
        amount=Decimal(amount),
        spent=Decimal(spent),
        remaining=Decimal(amount) - Decimal(spent),
        percent_used=float(Decimal(spent) / Decimal(amount) * 100),
        status=status,
    )


def test_overall_pace_warning_fires_when_projected_to_exceed():
    budget = make_budget(overall_amount="100.00", overall_spent="50.00", overall_status="ok")

    recs = _budget_recommendations(budget, fraction=Decimal("0.3"))

    assert len(recs) == 1
    assert recs[0].type == "budget_pace"
    assert recs[0].severity == "warning"
    assert "exceed your overall budget" in recs[0].message


def test_overall_pace_warning_does_not_fire_when_on_pace():
    budget = make_budget(overall_amount="100.00", overall_spent="50.00", overall_status="ok")

    recs = _budget_recommendations(budget, fraction=Decimal("0.9"))

    assert recs == []


def test_category_limit_pace_warning_fires_when_projected_to_exceed():
    limit = make_limit(amount="50.00", spent="30.00", status="ok")
    budget = make_budget(
        overall_amount=None, overall_spent="0", overall_status="ok", category_limits=[limit]
    )

    recs = _budget_recommendations(budget, fraction=Decimal("0.3"))

    assert len(recs) == 1
    assert recs[0].category_id == limit.category.id
    assert recs[0].severity == "warning"


def test_category_limit_pace_warning_does_not_fire_when_on_pace():
    limit = make_limit(amount="50.00", spent="30.00", status="ok")
    budget = make_budget(
        overall_amount=None, overall_spent="0", overall_status="ok", category_limits=[limit]
    )

    recs = _budget_recommendations(budget, fraction=Decimal("0.9"))

    assert recs == []


def test_already_exceeded_budget_is_critical_regardless_of_fraction():
    budget = make_budget(overall_amount="100.00", overall_spent="150.00", overall_status="exceeded")

    recs = _budget_recommendations(budget, fraction=Decimal("0.05"))

    assert len(recs) == 1
    assert recs[0].severity == "critical"


def test_category_trend_skips_when_previous_amount_below_floor(seeded_client, db_session):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    user_id = uuid.UUID(seeded_client.get("/users/me", headers=headers).json()["id"])
    today = date.today()

    seeded_client.post(
        "/transactions",
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": "15.00",
            "payee": "Store",
            "transaction_date": date(today.year, today.month, 1).isoformat(),
        },
        headers=headers,
    )

    recs = _category_trend_recommendations(db_session, user_id, today, fraction=Decimal("1"))

    assert recs == []


def _seed_month_expense(client, headers, category_id, amount, months_ago):
    today = date.today()
    month_start_year = today.year
    month_start_month = today.month - months_ago
    while month_start_month < 1:
        month_start_month += 12
        month_start_year -= 1
    return client.post(
        "/transactions",
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": amount,
            "payee": "Store",
            "transaction_date": date(month_start_year, month_start_month, 5).isoformat(),
        },
        headers=headers,
    )


def test_category_trend_skips_when_increase_below_dollar_floor(seeded_client, db_session):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    user_id = uuid.UUID(seeded_client.get("/users/me", headers=headers).json()["id"])
    today = date.today()

    _seed_month_expense(seeded_client, headers, category_id, "100.00", months_ago=1)
    _seed_month_expense(seeded_client, headers, category_id, "110.00", months_ago=0)

    recs = _category_trend_recommendations(db_session, user_id, today, fraction=Decimal("1"))

    assert recs == []


def test_category_trend_skips_when_increase_below_percent_floor(seeded_client, db_session):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    user_id = uuid.UUID(seeded_client.get("/users/me", headers=headers).json()["id"])
    today = date.today()

    _seed_month_expense(seeded_client, headers, category_id, "200.00", months_ago=1)
    _seed_month_expense(seeded_client, headers, category_id, "220.00", months_ago=0)

    recs = _category_trend_recommendations(db_session, user_id, today, fraction=Decimal("1"))

    assert recs == []


def test_category_trend_fires_when_both_floors_cleared(seeded_client, db_session):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    user_id = uuid.UUID(seeded_client.get("/users/me", headers=headers).json()["id"])
    today = date.today()

    _seed_month_expense(seeded_client, headers, category_id, "100.00", months_ago=1)
    _seed_month_expense(seeded_client, headers, category_id, "140.00", months_ago=0)

    recs = _category_trend_recommendations(db_session, user_id, today, fraction=Decimal("1"))

    assert len(recs) == 1
    assert recs[0].type == "category_trend"
    assert recs[0].category_id == uuid.UUID(category_id)

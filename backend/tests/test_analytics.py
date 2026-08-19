from datetime import date

import pytest

from app.models.enums import RecurringFrequency
from app.services.analytics_service import add_months, compute_next_due_date
from tests.helpers import get_category_id, register_and_login


def create_transaction(client, headers, category_id, **overrides):
    payload = {
        "type": "expense",
        "category_id": category_id,
        "amount": "50.00",
        "payee": "Test Merchant",
        "transaction_date": "2026-08-05",
        **overrides,
    }
    return client.post("/transactions", json=payload, headers=headers)


# --- Pure function unit tests -------------------------------------------------


def test_add_months_clamps_to_month_end():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


def test_add_months_handles_year_rollover():
    assert add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)
    assert add_months(date(2026, 1, 15), -1) == date(2025, 12, 15)


@pytest.mark.parametrize(
    ("frequency", "expected"),
    [
        (RecurringFrequency.WEEKLY, date(2026, 8, 8)),
        (RecurringFrequency.BIWEEKLY, date(2026, 8, 15)),
        (RecurringFrequency.MONTHLY, date(2026, 9, 1)),
        (RecurringFrequency.QUARTERLY, date(2026, 11, 1)),
        (RecurringFrequency.YEARLY, date(2027, 8, 1)),
    ],
)
def test_compute_next_due_date_per_frequency(frequency, expected):
    assert compute_next_due_date(date(2026, 8, 1), frequency) == expected


# --- API integration tests ----------------------------------------------------


def test_summary_reflects_income_and_expenses(seeded_client):
    headers = register_and_login(seeded_client)
    expense_category = get_category_id(seeded_client, headers, "expense")
    income_category = get_category_id(seeded_client, headers, "income")

    create_transaction(seeded_client, headers, expense_category, amount="300.00")
    create_transaction(
        seeded_client,
        headers,
        income_category,
        type="income",
        payee="Employer",
        amount="2000.00",
    )

    response = seeded_client.get(
        "/analytics/summary", params={"year": 2026, "month": 8}, headers=headers
    )

    body = response.json()
    assert body["income"] == "2000.00"
    assert body["expenses"] == "300.00"
    assert body["net_cash_flow"] == "1700.00"


def test_summary_month_over_month_change(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    create_transaction(
        seeded_client, headers, category_id, amount="100.00", transaction_date="2026-07-05"
    )
    create_transaction(
        seeded_client, headers, category_id, amount="150.00", transaction_date="2026-08-05"
    )

    response = seeded_client.get(
        "/analytics/summary", params={"year": 2026, "month": 8}, headers=headers
    )

    body = response.json()
    assert body["previous_month_expenses"] == "100.00"
    assert body["expenses_change_percent"] == 50.0


def test_summary_change_percent_is_null_with_no_previous_data(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    create_transaction(seeded_client, headers, category_id, transaction_date="2026-08-05")

    response = seeded_client.get(
        "/analytics/summary", params={"year": 2026, "month": 8}, headers=headers
    )

    assert response.json()["expenses_change_percent"] is None


def test_category_breakdown_percentages_and_sort_order(seeded_client):
    headers = register_and_login(seeded_client)
    categories = seeded_client.get(
        "/categories", params={"type": "expense"}, headers=headers
    ).json()
    cat_a, cat_b = categories[0]["id"], categories[1]["id"]

    create_transaction(seeded_client, headers, cat_a, amount="300.00")
    create_transaction(seeded_client, headers, cat_b, amount="100.00")

    response = seeded_client.get(
        "/analytics/categories", params={"year": 2026, "month": 8}, headers=headers
    )

    body = response.json()
    assert len(body) == 2
    assert body[0]["amount"] == "300.00"
    assert body[0]["percent_of_total"] == 75.0
    assert body[1]["percent_of_total"] == 25.0


def test_trends_returns_requested_number_of_months_in_order(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get("/analytics/trends", params={"months": 3}, headers=headers)

    body = response.json()
    assert len(body) == 3
    # chronological order: each entry's (year, month) should be strictly increasing
    keys = [(item["year"], item["month"]) for item in body]
    assert keys == sorted(keys)


def test_merchants_sorted_by_total_spend_descending(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    create_transaction(seeded_client, headers, category_id, payee="Big Spend", amount="500.00")
    create_transaction(seeded_client, headers, category_id, payee="Small Spend", amount="20.00")
    create_transaction(seeded_client, headers, category_id, payee="Small Spend", amount="20.00")

    response = seeded_client.get(
        "/analytics/merchants", params={"year": 2026, "month": 8}, headers=headers
    )

    body = response.json()
    assert body[0]["payee"] == "Big Spend"
    assert body[0]["total_amount"] == "500.00"
    second = next(m for m in body if m["payee"] == "Small Spend")
    assert second["total_amount"] == "40.00"
    assert second["transaction_count"] == 2


def test_recurring_analysis_projects_next_due_date_and_estimate(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    create_transaction(
        seeded_client,
        headers,
        category_id,
        payee="Netflix",
        amount="15.00",
        is_recurring=True,
        recurring_frequency="monthly",
        transaction_date="2026-08-01",
    )
    # A second occurrence of the same series - only the most recent should count
    create_transaction(
        seeded_client,
        headers,
        category_id,
        payee="Netflix",
        amount="15.00",
        is_recurring=True,
        recurring_frequency="monthly",
        transaction_date="2026-07-01",
    )

    response = seeded_client.get("/analytics/recurring", headers=headers)
    body = response.json()

    assert len(body["series"]) == 1
    item = body["series"][0]
    assert item["payee"] == "Netflix"
    assert item["last_date"] == "2026-08-01"
    assert item["next_due_date"] == "2026-09-01"
    assert body["total_monthly_estimate"] == "15.00"


def test_analytics_are_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")

    category_id = get_category_id(seeded_client, owner_headers, "expense")
    create_transaction(seeded_client, owner_headers, category_id, amount="999.00")

    response = seeded_client.get(
        "/analytics/summary", params={"year": 2026, "month": 8}, headers=other_headers
    )

    assert response.json()["expenses"] == "0"

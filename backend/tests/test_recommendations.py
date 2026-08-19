from datetime import date, timedelta

from app.services.analytics_service import add_months
from tests.helpers import get_category_id, register_and_login


def month_date(months_ago: int, day: int = 5) -> str:
    today = date.today()
    month_start = add_months(date(today.year, today.month, 1), -months_ago)
    return date(month_start.year, month_start.month, day).isoformat()


def create_expense(client, headers, category_id, amount, months_ago=0):
    return client.post(
        "/transactions",
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": amount,
            "payee": "Test Merchant",
            "transaction_date": month_date(months_ago),
        },
        headers=headers,
    )


def test_no_recommendations_for_new_user(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get("/recommendations", headers=headers)

    assert response.status_code == 200
    assert response.json()["recommendations"] == []


def test_exceeded_budget_produces_critical_recommendation(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    today = date.today()

    budget_response = seeded_client.post(
        "/budgets",
        json={"month": today.month, "year": today.year, "overall_amount": "100.00"},
        headers=headers,
    )
    assert budget_response.status_code == 201

    create_expense(seeded_client, headers, category_id, "150.00")

    response = seeded_client.get("/recommendations", headers=headers)
    recommendations = response.json()["recommendations"]

    critical = [r for r in recommendations if r["type"] == "budget_pace"]
    assert critical
    assert critical[0]["severity"] == "critical"
    assert "exceeded" in critical[0]["message"]


def test_exceeded_category_limit_produces_critical_recommendation(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    today = date.today()

    budget_response = seeded_client.post(
        "/budgets",
        json={
            "month": today.month,
            "year": today.year,
            "category_limits": [{"category_id": category_id, "amount": "50.00"}],
        },
        headers=headers,
    )
    assert budget_response.status_code == 201

    create_expense(seeded_client, headers, category_id, "75.00")

    response = seeded_client.get("/recommendations", headers=headers)
    recommendations = response.json()["recommendations"]

    critical = [r for r in recommendations if r["type"] == "budget_pace"]
    assert critical
    assert critical[0]["severity"] == "critical"
    assert critical[0]["category_id"] == category_id


def test_category_trend_recommendation_on_large_increase(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    create_expense(seeded_client, headers, category_id, "20.00", months_ago=1)
    create_expense(seeded_client, headers, category_id, "200.00", months_ago=0)

    response = seeded_client.get("/recommendations", headers=headers)
    recommendations = response.json()["recommendations"]

    trend = [r for r in recommendations if r["type"] == "category_trend"]
    assert trend
    assert trend[0]["severity"] == "info"
    assert trend[0]["category_id"] == category_id


def test_savings_goal_off_track_produces_warning(seeded_client):
    headers = register_and_login(seeded_client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    goal_response = seeded_client.post(
        "/savings-goals",
        json={
            "name": "Emergency Fund",
            "target_amount": "5000.00",
            "current_amount": "0",
            "target_date": yesterday,
        },
        headers=headers,
    )
    assert goal_response.status_code == 201
    goal_id = goal_response.json()["id"]

    response = seeded_client.get("/recommendations", headers=headers)
    recommendations = response.json()["recommendations"]

    off_track = [r for r in recommendations if r["type"] == "savings_off_track"]
    assert off_track
    assert off_track[0]["severity"] == "warning"
    assert off_track[0]["goal_id"] == goal_id


def test_recommendations_are_isolated_between_users(seeded_client):
    troubled_headers = register_and_login(seeded_client, email="troubled@example.com")
    category_id = get_category_id(seeded_client, troubled_headers, "expense")
    today = date.today()
    seeded_client.post(
        "/budgets",
        json={"month": today.month, "year": today.year, "overall_amount": "100.00"},
        headers=troubled_headers,
    )
    create_expense(seeded_client, troubled_headers, category_id, "150.00")

    other_headers = register_and_login(seeded_client, email="other@example.com")

    response = seeded_client.get("/recommendations", headers=other_headers)

    assert response.json()["recommendations"] == []

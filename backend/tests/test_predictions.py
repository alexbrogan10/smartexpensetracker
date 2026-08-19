from datetime import date

from app.services.analytics_service import add_months
from tests.helpers import get_category_id, register_and_login


def month_date(months_ago: int, day: int = 5) -> str:
    """ISO date `day` days into the month that was `months_ago` months before today."""
    today = date.today()
    month_start = add_months(date(today.year, today.month, 1), -months_ago)
    return date(month_start.year, month_start.month, day).isoformat()


def create_expense(client, headers, category_id, amount, months_ago):
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


def test_insufficient_data_for_new_user(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get("/predictions/spending", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["predicted_income"] is None
    assert body["predicted_expenses"] is None
    assert body["by_category"] == []


def test_predicts_expenses_once_enough_history_exists(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    for months_ago, amount in [(4, "100.00"), (3, "150.00"), (2, "200.00"), (1, "250.00")]:
        response = create_expense(seeded_client, headers, category_id, amount, months_ago)
        assert response.status_code == 201

    response = seeded_client.get("/predictions/spending", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert float(body["predicted_expenses"]) > 0
    assert len(body["next_month"]) == 7  # "YYYY-MM"

    assert body["by_category"]
    predicted_category = body["by_category"][0]
    assert predicted_category["category_id"] == category_id
    assert float(predicted_category["predicted_amount"]) > 0


def test_predictions_are_isolated_between_users(seeded_client):
    trained_headers = register_and_login(seeded_client, email="trained@example.com")
    category_id = get_category_id(seeded_client, trained_headers, "expense")
    for months_ago, amount in [(4, "100.00"), (3, "150.00"), (2, "200.00"), (1, "250.00")]:
        create_expense(seeded_client, trained_headers, category_id, amount, months_ago)

    new_user_headers = register_and_login(seeded_client, email="newuser@example.com")

    response = seeded_client.get("/predictions/spending", headers=new_user_headers)

    assert response.json()["status"] == "insufficient_data"

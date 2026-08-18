from tests.helpers import get_category_id, register_and_login


def create_expense(client, headers, category_id, amount, transaction_date="2026-08-05"):
    return client.post(
        "/transactions",
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": amount,
            "payee": "Test Merchant",
            "transaction_date": transaction_date,
        },
        headers=headers,
    )


def test_create_budget_with_overall_amount(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.post(
        "/budgets", json={"month": 8, "year": 2026, "overall_amount": "3000.00"}, headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["overall_amount"] == "3000.00"
    assert body["overall_spent"] == "0"
    assert body["overall_status"] == "ok"
    assert body["category_limits"] == []


def test_create_budget_with_category_limits(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    response = seeded_client.post(
        "/budgets",
        json={
            "month": 8,
            "year": 2026,
            "category_limits": [{"category_id": category_id, "amount": "400.00"}],
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["category_limits"]) == 1
    assert body["category_limits"][0]["amount"] == "400.00"
    assert body["category_limits"][0]["status"] == "ok"


def test_duplicate_month_year_budget_conflicts(seeded_client):
    headers = register_and_login(seeded_client)
    seeded_client.post("/budgets", json={"month": 8, "year": 2026}, headers=headers)

    response = seeded_client.post("/budgets", json={"month": 8, "year": 2026}, headers=headers)

    assert response.status_code == 409


def test_duplicate_category_in_same_request_rejected(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    response = seeded_client.post(
        "/budgets",
        json={
            "month": 8,
            "year": 2026,
            "category_limits": [
                {"category_id": category_id, "amount": "100.00"},
                {"category_id": category_id, "amount": "200.00"},
            ],
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_income_category_rejected_as_budget_category(seeded_client):
    headers = register_and_login(seeded_client)
    income_category_id = get_category_id(seeded_client, headers, "income")

    response = seeded_client.post(
        "/budgets",
        json={
            "month": 8,
            "year": 2026,
            "category_limits": [{"category_id": income_category_id, "amount": "100.00"}],
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_budget_progress_reflects_spending_and_thresholds(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    budget = seeded_client.post(
        "/budgets",
        json={
            "month": 8,
            "year": 2026,
            "overall_amount": "1000.00",
            "category_limits": [{"category_id": category_id, "amount": "100.00"}],
        },
        headers=headers,
    ).json()

    # Spend 85 of 100 in-category -> warning (>= 80%)
    create_expense(seeded_client, headers, category_id, "85.00")
    # An expense outside this budget's month shouldn't count
    create_expense(seeded_client, headers, category_id, "500.00", transaction_date="2026-01-01")

    response = seeded_client.get(f"/budgets/{budget['id']}", headers=headers)
    body = response.json()

    category_limit = body["category_limits"][0]
    assert category_limit["spent"] == "85.00"
    assert category_limit["remaining"] == "15.00"
    assert category_limit["status"] == "warning"
    assert body["overall_spent"] == "85.00"
    assert body["overall_status"] == "ok"


def test_budget_exceeded_status(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    budget = seeded_client.post(
        "/budgets",
        json={
            "month": 8,
            "year": 2026,
            "category_limits": [{"category_id": category_id, "amount": "50.00"}],
        },
        headers=headers,
    ).json()

    create_expense(seeded_client, headers, category_id, "75.00")

    response = seeded_client.get(f"/budgets/{budget['id']}", headers=headers)
    category_limit = response.json()["category_limits"][0]
    assert category_limit["status"] == "exceeded"
    assert category_limit["remaining"] == "-25.00"


def test_get_current_budget_returns_null_when_none_exists(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get("/budgets/current", headers=headers)

    assert response.status_code == 200
    assert response.json() is None


def test_list_budgets_filters_by_year(seeded_client):
    headers = register_and_login(seeded_client)
    seeded_client.post("/budgets", json={"month": 1, "year": 2025}, headers=headers)
    seeded_client.post("/budgets", json={"month": 1, "year": 2026}, headers=headers)

    response = seeded_client.get("/budgets", params={"year": 2026}, headers=headers)

    budgets = response.json()
    assert len(budgets) == 1
    assert budgets[0]["year"] == 2026


def test_update_budget_replaces_category_limits(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    budget = seeded_client.post(
        "/budgets",
        json={
            "month": 8,
            "year": 2026,
            "category_limits": [{"category_id": category_id, "amount": "100.00"}],
        },
        headers=headers,
    ).json()

    response = seeded_client.put(
        f"/budgets/{budget['id']}",
        json={"overall_amount": "2000.00", "category_limits": []},
        headers=headers,
    )

    body = response.json()
    assert body["overall_amount"] == "2000.00"
    assert body["category_limits"] == []


def test_delete_budget(seeded_client):
    headers = register_and_login(seeded_client)
    budget = seeded_client.post("/budgets", json={"month": 8, "year": 2026}, headers=headers).json()

    delete_response = seeded_client.delete(f"/budgets/{budget['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = seeded_client.get(f"/budgets/{budget['id']}", headers=headers)
    assert get_response.status_code == 404


def test_budgets_are_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")

    budget = seeded_client.post(
        "/budgets", json={"month": 8, "year": 2026}, headers=owner_headers
    ).json()

    other_list = seeded_client.get("/budgets", headers=other_headers).json()
    assert other_list == []

    assert seeded_client.get(f"/budgets/{budget['id']}", headers=other_headers).status_code == 404
    assert (
        seeded_client.put(
            f"/budgets/{budget['id']}", json={"overall_amount": "1.00"}, headers=other_headers
        ).status_code
        == 404
    )
    assert (
        seeded_client.delete(f"/budgets/{budget['id']}", headers=other_headers).status_code == 404
    )

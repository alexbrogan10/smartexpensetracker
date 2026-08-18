from tests.helpers import get_category_id, register_and_login


def create_transaction(client, headers, category_id, **overrides):
    payload = {
        "type": "expense",
        "category_id": category_id,
        "amount": "42.50",
        "payee": "Trader Joe's",
        "transaction_date": "2026-08-01",
        **overrides,
    }
    return client.post("/transactions", json=payload, headers=headers)


def test_create_expense_transaction(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    response = create_transaction(seeded_client, headers, category_id)

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "42.50"
    assert body["category"]["id"] == category_id


def test_create_income_transaction(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "income")

    response = create_transaction(
        seeded_client,
        headers,
        category_id,
        type="income",
        payee="Employer Inc",
        amount="2500.00",
    )

    assert response.status_code == 201
    assert response.json()["type"] == "income"


def test_create_transaction_with_mismatched_category_type_fails(seeded_client):
    headers = register_and_login(seeded_client)
    income_category_id = get_category_id(seeded_client, headers, "income")

    response = create_transaction(seeded_client, headers, income_category_id, type="expense")

    assert response.status_code == 422


def test_create_recurring_transaction_without_frequency_fails(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    response = create_transaction(seeded_client, headers, category_id, is_recurring=True)

    assert response.status_code == 422


def test_create_recurring_transaction_with_frequency_succeeds(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    response = create_transaction(
        seeded_client,
        headers,
        category_id,
        is_recurring=True,
        recurring_frequency="monthly",
    )

    assert response.status_code == 201


def test_list_transactions_paginates(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    for i in range(5):
        create_transaction(
            seeded_client, headers, category_id, transaction_date=f"2026-08-{i + 1:02d}"
        )

    response = seeded_client.get(
        "/transactions", params={"page": 1, "page_size": 2}, headers=headers
    )

    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2
    # default sort is transaction_date desc
    assert body["items"][0]["transaction_date"] == "2026-08-05"


def test_list_transactions_filters_by_type(seeded_client):
    headers = register_and_login(seeded_client)
    expense_category_id = get_category_id(seeded_client, headers, "expense")
    income_category_id = get_category_id(seeded_client, headers, "income")
    create_transaction(seeded_client, headers, expense_category_id)
    create_transaction(seeded_client, headers, income_category_id, type="income", payee="Employer")

    response = seeded_client.get("/transactions", params={"type": "income"}, headers=headers)

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "income"


def test_list_transactions_filters_by_date_range(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    create_transaction(seeded_client, headers, category_id, transaction_date="2026-01-15")
    create_transaction(seeded_client, headers, category_id, transaction_date="2026-08-15")

    response = seeded_client.get(
        "/transactions",
        params={"date_from": "2026-08-01", "date_to": "2026-08-31"},
        headers=headers,
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["transaction_date"] == "2026-08-15"


def test_list_transactions_filters_by_amount_range(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    create_transaction(seeded_client, headers, category_id, amount="10.00")
    create_transaction(seeded_client, headers, category_id, amount="500.00")

    response = seeded_client.get(
        "/transactions", params={"min_amount": "100", "max_amount": "1000"}, headers=headers
    )

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["amount"] == "500.00"


def test_list_transactions_search_matches_payee(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    create_transaction(seeded_client, headers, category_id, payee="Trader Joe's")
    create_transaction(seeded_client, headers, category_id, payee="Shell Gas Station")

    response = seeded_client.get("/transactions", params={"search": "trader"}, headers=headers)

    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["payee"] == "Trader Joe's"


def test_update_transaction(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    created = create_transaction(seeded_client, headers, category_id).json()

    response = seeded_client.put(
        f"/transactions/{created['id']}", json={"amount": "99.99"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["amount"] == "99.99"


def test_update_transaction_with_mismatched_category_fails(seeded_client):
    headers = register_and_login(seeded_client)
    expense_category_id = get_category_id(seeded_client, headers, "expense")
    income_category_id = get_category_id(seeded_client, headers, "income")
    created = create_transaction(seeded_client, headers, expense_category_id).json()

    response = seeded_client.put(
        f"/transactions/{created['id']}",
        json={"category_id": income_category_id},
        headers=headers,
    )

    assert response.status_code == 422


def test_delete_transaction(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    created = create_transaction(seeded_client, headers, category_id).json()

    delete_response = seeded_client.delete(f"/transactions/{created['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = seeded_client.get(f"/transactions/{created['id']}", headers=headers)
    assert get_response.status_code == 404


def test_get_nonexistent_transaction_returns_404(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get(
        "/transactions/00000000-0000-0000-0000-000000000000", headers=headers
    )

    assert response.status_code == 404


def test_delete_category_with_transactions_conflicts(seeded_client):
    headers = register_and_login(seeded_client)
    custom_category = seeded_client.post(
        "/categories", json={"name": "Pet Care", "type": "expense"}, headers=headers
    ).json()
    create_transaction(seeded_client, headers, custom_category["id"])

    response = seeded_client.delete(f"/categories/{custom_category['id']}", headers=headers)

    assert response.status_code == 409


def test_transactions_are_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")

    owner_category_id = get_category_id(seeded_client, owner_headers, "expense")
    created = create_transaction(seeded_client, owner_headers, owner_category_id).json()

    # Other user's list is empty
    other_list = seeded_client.get("/transactions", headers=other_headers).json()
    assert other_list["total"] == 0

    # Other user cannot read, update, or delete owner's transaction
    other_get = seeded_client.get(f"/transactions/{created['id']}", headers=other_headers)
    assert other_get.status_code == 404
    assert (
        seeded_client.put(
            f"/transactions/{created['id']}", json={"amount": "1.00"}, headers=other_headers
        ).status_code
        == 404
    )
    assert (
        seeded_client.delete(f"/transactions/{created['id']}", headers=other_headers).status_code
        == 404
    )

    # Owner still sees their own transaction untouched
    owner_get = seeded_client.get(f"/transactions/{created['id']}", headers=owner_headers)
    assert owner_get.status_code == 200
    assert owner_get.json()["amount"] == "42.50"

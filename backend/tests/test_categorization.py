from app.ml.categorization import MIN_TRANSACTIONS
from tests.helpers import register_and_login


def get_category(client, headers, type_: str, name: str) -> dict:
    categories = client.get("/categories", params={"type": type_}, headers=headers).json()
    return next(c for c in categories if c["name"] == name)


def create_transaction(client, headers, category_id, payee, type_="expense", amount="12.00"):
    payload = {
        "type": type_,
        "category_id": category_id,
        "amount": amount,
        "payee": payee,
        "transaction_date": "2026-08-01",
    }
    response = client.post("/transactions", json=payload, headers=headers)
    assert response.status_code == 201
    return response


def suggest(client, headers, type_, payee, description=None):
    return client.post(
        "/categorization/suggest",
        json={"type": type_, "payee": payee, "description": description},
        headers=headers,
    )


def test_insufficient_data_for_new_user(seeded_client):
    headers = register_and_login(seeded_client)

    response = suggest(seeded_client, headers, "expense", "Whole Foods")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_data"
    assert body["suggestions"] == []


def test_suggests_correct_category_once_trained(seeded_client):
    headers = register_and_login(seeded_client)
    groceries = get_category(seeded_client, headers, "expense", "Groceries")
    restaurants = get_category(seeded_client, headers, "expense", "Restaurants")

    for _ in range(MIN_TRANSACTIONS):
        create_transaction(seeded_client, headers, groceries["id"], "Whole Foods")
        create_transaction(seeded_client, headers, restaurants["id"], "Chipotle")

    response = suggest(seeded_client, headers, "expense", "Whole Foods")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["suggestions"][0]["category_id"] == groceries["id"]
    assert body["suggestions"][0]["category_name"] == "Groceries"
    assert 0.0 < body["suggestions"][0]["confidence"] <= 1.0


def test_suggestion_scoped_to_transaction_type(seeded_client):
    headers = register_and_login(seeded_client)
    groceries = get_category(seeded_client, headers, "expense", "Groceries")
    restaurants = get_category(seeded_client, headers, "expense", "Restaurants")

    for _ in range(MIN_TRANSACTIONS):
        create_transaction(seeded_client, headers, groceries["id"], "Whole Foods")
        create_transaction(seeded_client, headers, restaurants["id"], "Chipotle")

    response = suggest(seeded_client, headers, "income", "Whole Foods")

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


def test_suggestion_isolated_between_users(seeded_client):
    trained_headers = register_and_login(seeded_client, email="trained@example.com")
    groceries = get_category(seeded_client, trained_headers, "expense", "Groceries")
    restaurants = get_category(seeded_client, trained_headers, "expense", "Restaurants")
    for _ in range(MIN_TRANSACTIONS):
        create_transaction(seeded_client, trained_headers, groceries["id"], "Whole Foods")
        create_transaction(seeded_client, trained_headers, restaurants["id"], "Chipotle")

    new_user_headers = register_and_login(seeded_client, email="newuser@example.com")

    response = suggest(seeded_client, new_user_headers, "expense", "Whole Foods")

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"

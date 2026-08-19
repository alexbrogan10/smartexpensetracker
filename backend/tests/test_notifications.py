from tests.helpers import get_category_id, register_and_login

NORMAL_AMOUNTS = ["50.00", "52.00", "48.00", "51.00", "49.00"]


def create_expense(client, headers, category_id, amount, payee="Test Merchant"):
    return client.post(
        "/transactions",
        json={
            "type": "expense",
            "category_id": category_id,
            "amount": amount,
            "payee": payee,
            "transaction_date": "2026-08-05",
        },
        headers=headers,
    )


def seed_normal_history(client, headers, category_id):
    for amount in NORMAL_AMOUNTS:
        response = create_expense(client, headers, category_id, amount)
        assert response.status_code == 201


def test_normal_transaction_creates_no_notification(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    seed_normal_history(seeded_client, headers, category_id)

    create_expense(seeded_client, headers, category_id, "53.00")

    response = seeded_client.get("/notifications", headers=headers)
    assert response.json()["total"] == 0


def test_unusual_transaction_creates_notification(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    seed_normal_history(seeded_client, headers, category_id)

    outlier = create_expense(seeded_client, headers, category_id, "500.00", payee="Big Purchase")
    assert outlier.status_code == 201
    transaction_id = outlier.json()["id"]

    response = seeded_client.get("/notifications", headers=headers)
    body = response.json()

    assert body["total"] == 1
    notification = body["items"][0]
    assert notification["type"] == "unusual_spending"
    assert notification["related_transaction_id"] == transaction_id
    assert notification["is_read"] is False
    assert "Big Purchase" in notification["message"]


def test_first_five_transactions_never_flagged_regardless_of_amount(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")

    for amount in ["10.00", "5000.00", "8.00", "3000.00", "12.00"]:
        create_expense(seeded_client, headers, category_id, amount)

    response = seeded_client.get("/notifications", headers=headers)
    assert response.json()["total"] == 0


def test_unread_count_endpoint(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    seed_normal_history(seeded_client, headers, category_id)
    create_expense(seeded_client, headers, category_id, "500.00")

    response = seeded_client.get("/notifications/unread-count", headers=headers)
    assert response.json()["count"] == 1


def test_mark_as_read(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    seed_normal_history(seeded_client, headers, category_id)
    create_expense(seeded_client, headers, category_id, "500.00")

    notification_id = seeded_client.get("/notifications", headers=headers).json()["items"][0]["id"]

    response = seeded_client.patch(f"/notifications/{notification_id}/read", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_read"] is True

    unread = seeded_client.get("/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 0

    unread_only = seeded_client.get("/notifications", params={"unread_only": True}, headers=headers)
    assert unread_only.json()["total"] == 0


def test_mark_as_read_404_for_other_users_notification(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    category_id = get_category_id(seeded_client, owner_headers, "expense")
    seed_normal_history(seeded_client, owner_headers, category_id)
    create_expense(seeded_client, owner_headers, category_id, "500.00")
    notification_id = seeded_client.get("/notifications", headers=owner_headers).json()["items"][0][
        "id"
    ]

    other_headers = register_and_login(seeded_client, email="other@example.com")
    response = seeded_client.patch(f"/notifications/{notification_id}/read", headers=other_headers)

    assert response.status_code == 404


def test_mark_all_as_read(seeded_client):
    headers = register_and_login(seeded_client)
    categories = seeded_client.get(
        "/categories", params={"type": "expense"}, headers=headers
    ).json()
    cat_a, cat_b = categories[0]["id"], categories[1]["id"]

    seed_normal_history(seeded_client, headers, cat_a)
    create_expense(seeded_client, headers, cat_a, "500.00")
    seed_normal_history(seeded_client, headers, cat_b)
    create_expense(seeded_client, headers, cat_b, "500.00")

    response = seeded_client.post("/notifications/read-all", headers=headers)
    assert response.json()["marked_read"] == 2

    unread = seeded_client.get("/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 0


def test_notifications_are_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner2@example.com")
    category_id = get_category_id(seeded_client, owner_headers, "expense")
    seed_normal_history(seeded_client, owner_headers, category_id)
    create_expense(seeded_client, owner_headers, category_id, "500.00")

    other_headers = register_and_login(seeded_client, email="other2@example.com")
    response = seeded_client.get("/notifications", headers=other_headers)

    assert response.json()["total"] == 0


def test_csv_import_flags_unusual_row(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    seed_normal_history(seeded_client, headers, category_id)

    category_name = next(
        c["name"]
        for c in seeded_client.get(
            "/categories", params={"type": "expense"}, headers=headers
        ).json()
        if c["id"] == category_id
    )
    csv_text = (
        f"date,type,category,payee,amount\n2026-08-10,expense,{category_name},Huge One-Off,900.00\n"
    )
    upload = seeded_client.post(
        "/imports/transactions",
        headers=headers,
        files={"file": ("transactions.csv", csv_text.encode(), "text/csv")},
    )
    assert upload.status_code == 201
    import_id = upload.json()["id"]

    confirm = seeded_client.post(
        f"/imports/transactions/{import_id}/confirm", json={}, headers=headers
    )
    assert confirm.status_code == 200
    assert confirm.json()["imported_count"] == 1

    response = seeded_client.get("/notifications", headers=headers)
    body = response.json()
    assert body["total"] == 1
    assert "Huge One-Off" in body["items"][0]["message"]

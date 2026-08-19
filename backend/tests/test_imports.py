from tests.helpers import register_and_login


def upload_csv(client, headers, csv_text: str, filename="transactions.csv"):
    return client.post(
        "/imports/transactions",
        headers=headers,
        files={"file": (filename, csv_text.encode(), "text/csv")},
    )


VALID_CSV = """date,type,category,payee,amount,description
2026-08-01,expense,Groceries,Whole Foods,42.50,weekly shop
2026-08-02,income,Salary,Employer,3000,
"""


def test_preview_valid_csv(seeded_client):
    headers = register_and_login(seeded_client)

    response = upload_csv(seeded_client, headers, VALID_CSV)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["total_rows"] == 2
    assert body["valid_rows"] == 2
    assert body["error_rows"] == 0
    assert body["duplicate_rows"] == 0
    assert all(r["status"] == "valid" for r in body["rows"])


def test_missing_required_column_rejected(seeded_client):
    headers = register_and_login(seeded_client)

    response = upload_csv(seeded_client, headers, "foo,bar\n1,2\n")

    assert response.status_code == 422


def test_non_csv_file_rejected(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.post(
        "/imports/transactions",
        headers=headers,
        files={"file": ("data.txt", b"not a csv", "text/plain")},
    )

    assert response.status_code == 422


def test_invalid_date_flagged_as_error(seeded_client):
    headers = register_and_login(seeded_client)
    csv_text = "date,type,category,payee,amount\nnot-a-date,expense,Groceries,Store,10.00\n"

    response = upload_csv(seeded_client, headers, csv_text)

    row = response.json()["rows"][0]
    assert row["status"] == "error"
    assert any("invalid date" in e for e in row["errors"])


def test_negative_and_invalid_amount_flagged_as_error(seeded_client):
    headers = register_and_login(seeded_client)
    csv_text = (
        "date,type,category,payee,amount\n"
        "2026-08-01,expense,Groceries,Store,-5.00\n"
        "2026-08-02,expense,Groceries,Store,notanumber\n"
    )

    response = upload_csv(seeded_client, headers, csv_text)

    rows = response.json()["rows"]
    assert rows[0]["status"] == "error"
    assert any("positive" in e for e in rows[0]["errors"])
    assert rows[1]["status"] == "error"
    assert any("invalid amount" in e for e in rows[1]["errors"])


def test_unknown_category_flagged_as_error(seeded_client):
    headers = register_and_login(seeded_client)
    csv_text = "date,type,category,payee,amount\n2026-08-01,expense,NotACategory,Store,10.00\n"

    response = upload_csv(seeded_client, headers, csv_text)

    row = response.json()["rows"][0]
    assert row["status"] == "error"
    assert any("unknown expense category" in e for e in row["errors"])


def test_missing_payee_flagged_as_error(seeded_client):
    headers = register_and_login(seeded_client)
    csv_text = "date,type,category,payee,amount\n2026-08-01,expense,Groceries,,10.00\n"

    response = upload_csv(seeded_client, headers, csv_text)

    row = response.json()["rows"][0]
    assert row["status"] == "error"
    assert "payee is required" in row["errors"]


def test_confirm_creates_transactions_and_skips_errors(seeded_client):
    headers = register_and_login(seeded_client)
    csv_text = VALID_CSV + "2026-08-03,expense,NotACategory,Store,10.00\n"
    preview = upload_csv(seeded_client, headers, csv_text).json()

    response = seeded_client.post(
        f"/imports/transactions/{preview['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["imported_count"] == 2
    assert body["skipped_count"] == 1

    listed = seeded_client.get("/transactions", headers=headers).json()
    assert listed["total"] == 2


def test_confirm_excludes_duplicates_by_default(seeded_client):
    headers = register_and_login(seeded_client)
    first = upload_csv(seeded_client, headers, VALID_CSV).json()
    seeded_client.post(
        f"/imports/transactions/{first['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    )

    second = upload_csv(seeded_client, headers, VALID_CSV).json()
    assert second["duplicate_rows"] == 2

    result = seeded_client.post(
        f"/imports/transactions/{second['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    ).json()
    assert result["imported_count"] == 0
    assert result["skipped_count"] == 2

    listed = seeded_client.get("/transactions", headers=headers).json()
    assert listed["total"] == 2


def test_confirm_includes_duplicates_when_requested(seeded_client):
    headers = register_and_login(seeded_client)
    first = upload_csv(seeded_client, headers, VALID_CSV).json()
    seeded_client.post(
        f"/imports/transactions/{first['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    )

    second = upload_csv(seeded_client, headers, VALID_CSV).json()
    result = seeded_client.post(
        f"/imports/transactions/{second['id']}/confirm",
        json={"include_duplicates": True},
        headers=headers,
    ).json()

    assert result["imported_count"] == 2
    listed = seeded_client.get("/transactions", headers=headers).json()
    assert listed["total"] == 4


def test_cancel_prevents_confirm(seeded_client):
    headers = register_and_login(seeded_client)
    preview = upload_csv(seeded_client, headers, VALID_CSV).json()

    delete_response = seeded_client.delete(
        f"/imports/transactions/{preview['id']}", headers=headers
    )
    assert delete_response.status_code == 204

    confirm_response = seeded_client.post(
        f"/imports/transactions/{preview['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    )
    assert confirm_response.status_code == 404


def test_confirm_twice_conflicts(seeded_client):
    headers = register_and_login(seeded_client)
    preview = upload_csv(seeded_client, headers, VALID_CSV).json()

    seeded_client.post(
        f"/imports/transactions/{preview['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    )
    second_confirm = seeded_client.post(
        f"/imports/transactions/{preview['id']}/confirm",
        json={"include_duplicates": False},
        headers=headers,
    )

    assert second_confirm.status_code == 409


def test_row_cap_exceeded_rejected(seeded_client):
    headers = register_and_login(seeded_client)
    lines = ["date,type,category,payee,amount"]
    for i in range(1001):
        lines.append(f"2026-08-01,expense,Groceries,Store {i},1.00")
    csv_text = "\n".join(lines) + "\n"

    response = upload_csv(seeded_client, headers, csv_text)

    assert response.status_code == 422


def test_imports_are_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")

    preview = upload_csv(seeded_client, owner_headers, VALID_CSV).json()

    get_response = seeded_client.get(
        f"/imports/transactions/{preview['id']}", headers=other_headers
    )
    assert get_response.status_code == 404
    assert (
        seeded_client.post(
            f"/imports/transactions/{preview['id']}/confirm",
            json={"include_duplicates": False},
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        seeded_client.delete(
            f"/imports/transactions/{preview['id']}", headers=other_headers
        ).status_code
        == 404
    )

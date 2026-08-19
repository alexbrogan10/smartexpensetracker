import io

import openpyxl

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


def test_export_csv_contains_expected_rows(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    create_transaction(seeded_client, headers, category_id, payee="Whole Foods", amount="20.00")
    create_transaction(seeded_client, headers, category_id, payee="Costco", amount="80.00")

    response = seeded_client.get("/reports/export", params={"format": "csv"}, headers=headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.content.decode()
    lines = text.strip().splitlines()
    expected_header = (
        "date,type,category,payee,amount,description,payment_method,"
        "is_recurring,recurring_frequency"
    )
    assert lines[0] == expected_header
    assert len(lines) == 3
    assert "Whole Foods" in text
    assert "Costco" in text


def test_export_respects_filters(seeded_client):
    headers = register_and_login(seeded_client)
    expense_category = get_category_id(seeded_client, headers, "expense")
    income_category = get_category_id(seeded_client, headers, "income")
    create_transaction(seeded_client, headers, expense_category, payee="Whole Foods")
    create_transaction(seeded_client, headers, income_category, type="income", payee="Employer")

    response = seeded_client.get(
        "/reports/export", params={"format": "csv", "type": "income"}, headers=headers
    )

    text = response.content.decode()
    assert "Employer" in text
    assert "Whole Foods" not in text


def test_export_xlsx_is_a_valid_workbook(seeded_client):
    headers = register_and_login(seeded_client)
    category_id = get_category_id(seeded_client, headers, "expense")
    create_transaction(seeded_client, headers, category_id, payee="Whole Foods")

    response = seeded_client.get("/reports/export", params={"format": "xlsx"}, headers=headers)

    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    workbook = openpyxl.load_workbook(io.BytesIO(response.content))
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    assert rows[0][0] == "date"
    assert any(row[3] == "Whole Foods" for row in rows[1:])


def test_export_is_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")
    category_id = get_category_id(seeded_client, owner_headers, "expense")
    create_transaction(seeded_client, owner_headers, category_id, payee="Owner Only")

    response = seeded_client.get("/reports/export", params={"format": "csv"}, headers=other_headers)

    text = response.content.decode()
    assert "Owner Only" not in text

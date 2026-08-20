from tests.helpers import register_and_login


def test_list_categories_returns_defaults(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get("/categories", headers=headers)

    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 19
    assert all(c["is_default"] for c in categories)
    assert all(c["user_id"] is None for c in categories)


def test_list_categories_filters_by_type(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.get("/categories", params={"type": "income"}, headers=headers)

    categories = response.json()
    assert len(categories) == 5
    assert all(c["type"] == "income" for c in categories)


def test_create_custom_category(seeded_client):
    headers = register_and_login(seeded_client)

    response = seeded_client.post(
        "/categories", json={"name": "Side Hustle", "type": "income"}, headers=headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Side Hustle"
    assert body["is_default"] is False
    assert body["user_id"] is not None


def test_create_duplicate_category_conflicts(seeded_client):
    headers = register_and_login(seeded_client)
    seeded_client.post(
        "/categories", json={"name": "Side Hustle", "type": "income"}, headers=headers
    )

    response = seeded_client.post(
        "/categories", json={"name": "Side Hustle", "type": "income"}, headers=headers
    )

    assert response.status_code == 409


def test_cannot_modify_default_category(seeded_client):
    headers = register_and_login(seeded_client)
    default_id = seeded_client.get("/categories", headers=headers).json()[0]["id"]

    response = seeded_client.put(
        f"/categories/{default_id}", json={"name": "Renamed"}, headers=headers
    )

    assert response.status_code == 403


def test_cannot_delete_default_category(seeded_client):
    headers = register_and_login(seeded_client)
    default_id = seeded_client.get("/categories", headers=headers).json()[0]["id"]

    response = seeded_client.delete(f"/categories/{default_id}", headers=headers)

    assert response.status_code == 403


def test_update_and_delete_custom_category(seeded_client):
    headers = register_and_login(seeded_client)
    created = seeded_client.post(
        "/categories", json={"name": "Side Hustle", "type": "income"}, headers=headers
    ).json()

    update_response = seeded_client.put(
        f"/categories/{created['id']}", json={"name": "Consulting"}, headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Consulting"

    delete_response = seeded_client.delete(f"/categories/{created['id']}", headers=headers)
    assert delete_response.status_code == 204


def test_update_category_icon_and_color(seeded_client):
    headers = register_and_login(seeded_client)
    created = seeded_client.post(
        "/categories", json={"name": "Side Hustle", "type": "income"}, headers=headers
    ).json()

    response = seeded_client.put(
        f"/categories/{created['id']}",
        json={"icon": "Work", "color": "#123456"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["icon"] == "Work"
    assert body["color"] == "#123456"


def test_rename_category_conflicts_with_existing_name(seeded_client):
    headers = register_and_login(seeded_client)
    seeded_client.post(
        "/categories", json={"name": "Consulting", "type": "income"}, headers=headers
    )
    other = seeded_client.post(
        "/categories", json={"name": "Side Hustle", "type": "income"}, headers=headers
    ).json()

    response = seeded_client.put(
        f"/categories/{other['id']}", json={"name": "Consulting"}, headers=headers
    )

    assert response.status_code == 409


def test_category_not_visible_to_other_user(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")

    created = seeded_client.post(
        "/categories", json={"name": "Owner Only", "type": "expense"}, headers=owner_headers
    ).json()

    response = seeded_client.put(
        f"/categories/{created['id']}", json={"name": "Hijacked"}, headers=other_headers
    )
    assert response.status_code == 404

    delete_response = seeded_client.delete(f"/categories/{created['id']}", headers=other_headers)
    assert delete_response.status_code == 404

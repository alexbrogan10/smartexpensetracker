REGISTER_PAYLOAD = {
    "email": "jane@example.com",
    "password": "supersecret123",
    "full_name": "Jane Doe",
}


def register(client, **overrides):
    payload = {**REGISTER_PAYLOAD, **overrides}
    return client.post("/auth/register", json=payload)


def login(client, email=REGISTER_PAYLOAD["email"], password=REGISTER_PAYLOAD["password"]):
    return client.post("/auth/login", data={"username": email, "password": password})


def auth_headers(client) -> dict[str, str]:
    token = login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == REGISTER_PAYLOAD["email"]
    assert body["full_name"] == REGISTER_PAYLOAD["full_name"]
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    register(client)

    response = register(client, full_name="Someone Else")

    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = register(client, password="short")

    assert response.status_code == 422


def test_login_returns_access_token(client):
    register(client)

    response = login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    register(client)

    response = login(client, password="wrong-password")

    assert response.status_code == 401


def test_login_unknown_email_rejected(client):
    response = login(client, email="nobody@example.com")

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_me_returns_current_user(client):
    register(client)

    response = client.get("/users/me", headers=auth_headers(client))

    assert response.status_code == 200
    assert response.json()["email"] == REGISTER_PAYLOAD["email"]


def test_update_profile_changes_full_name(client):
    register(client)

    response = client.put(
        "/users/me", json={"full_name": "Jane R. Doe"}, headers=auth_headers(client)
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane R. Doe"


def test_change_password_then_login_with_new_password(client):
    register(client)
    headers = auth_headers(client)

    response = client.post(
        "/users/me/change-password",
        json={"current_password": REGISTER_PAYLOAD["password"], "new_password": "newpassword456"},
        headers=headers,
    )
    assert response.status_code == 204

    assert login(client, password=REGISTER_PAYLOAD["password"]).status_code == 401
    assert login(client, password="newpassword456").status_code == 200


def test_change_password_rejects_wrong_current_password(client):
    register(client)

    response = client.post(
        "/users/me/change-password",
        json={"current_password": "wrong-current", "new_password": "newpassword456"},
        headers=auth_headers(client),
    )

    assert response.status_code == 400

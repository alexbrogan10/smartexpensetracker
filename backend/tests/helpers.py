def register_and_login(
    client, email="user@example.com", password="password123", full_name="Test User"
) -> dict[str, str]:
    client.post(
        "/auth/register", json={"email": email, "password": password, "full_name": full_name}
    )
    response = client.post("/auth/login", data={"username": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

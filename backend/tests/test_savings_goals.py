from datetime import date, timedelta

from tests.helpers import register_and_login


def create_goal(client, headers, **overrides):
    payload = {
        "name": "Emergency Fund",
        "target_amount": "5000.00",
        **overrides,
    }
    return client.post("/savings-goals", json=payload, headers=headers)


def test_create_savings_goal(seeded_client):
    headers = register_and_login(seeded_client)

    response = create_goal(seeded_client, headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Emergency Fund"
    assert body["current_amount"] == "0.00"
    assert body["progress_percentage"] == 0.0
    assert body["is_on_track"] is None


def test_target_amount_must_be_positive(seeded_client):
    headers = register_and_login(seeded_client)

    response = create_goal(seeded_client, headers, target_amount="0")

    assert response.status_code == 422


def test_progress_percentage_is_computed_and_capped(seeded_client):
    headers = register_and_login(seeded_client)
    created = create_goal(
        seeded_client, headers, target_amount="1000.00", current_amount="250.00"
    ).json()
    assert created["progress_percentage"] == 25.0

    over_saved = create_goal(
        seeded_client, headers, name="Vacation", target_amount="1000.00", current_amount="1500.00"
    ).json()
    assert over_saved["progress_percentage"] == 100.0


def test_on_track_true_when_far_from_deadline_and_on_pace(seeded_client):
    headers = register_and_login(seeded_client)
    far_future = (date.today() + timedelta(days=365)).isoformat()

    created = create_goal(seeded_client, headers, current_amount="0", target_date=far_future).json()

    assert created["is_on_track"] is True


def test_on_track_false_when_deadline_passed_and_goal_not_met(seeded_client):
    headers = register_and_login(seeded_client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    created = create_goal(
        seeded_client, headers, current_amount="100.00", target_date=yesterday
    ).json()

    assert created["is_on_track"] is False


def test_on_track_true_when_deadline_passed_but_goal_met(seeded_client):
    headers = register_and_login(seeded_client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    created = create_goal(
        seeded_client,
        headers,
        target_amount="500.00",
        current_amount="500.00",
        target_date=yesterday,
    ).json()

    assert created["is_on_track"] is True


def test_update_savings_goal_current_amount(seeded_client):
    headers = register_and_login(seeded_client)
    created = create_goal(seeded_client, headers).json()

    response = seeded_client.put(
        f"/savings-goals/{created['id']}", json={"current_amount": "1200.00"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["current_amount"] == "1200.00"
    assert body["progress_percentage"] == 24.0


def test_list_savings_goals(seeded_client):
    headers = register_and_login(seeded_client)
    create_goal(seeded_client, headers, name="Emergency Fund")
    create_goal(seeded_client, headers, name="Vacation")

    response = seeded_client.get("/savings-goals", headers=headers)

    names = {g["name"] for g in response.json()}
    assert names == {"Emergency Fund", "Vacation"}


def test_delete_savings_goal(seeded_client):
    headers = register_and_login(seeded_client)
    created = create_goal(seeded_client, headers).json()

    delete_response = seeded_client.delete(f"/savings-goals/{created['id']}", headers=headers)
    assert delete_response.status_code == 204

    get_response = seeded_client.get(f"/savings-goals/{created['id']}", headers=headers)
    assert get_response.status_code == 404


def test_savings_goals_are_isolated_between_users(seeded_client):
    owner_headers = register_and_login(seeded_client, email="owner@example.com")
    other_headers = register_and_login(seeded_client, email="other@example.com")

    created = create_goal(seeded_client, owner_headers).json()

    other_list = seeded_client.get("/savings-goals", headers=other_headers).json()
    assert other_list == []

    assert (
        seeded_client.get(f"/savings-goals/{created['id']}", headers=other_headers).status_code
        == 404
    )
    assert (
        seeded_client.put(
            f"/savings-goals/{created['id']}",
            json={"current_amount": "1.00"},
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        seeded_client.delete(f"/savings-goals/{created['id']}", headers=other_headers).status_code
        == 404
    )

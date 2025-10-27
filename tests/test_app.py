import sys
import os
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

# Ensure 'src' is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import app as tested_app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(tested_app.app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Expect at least one known activity
    assert "Chess Club" in data


def test_signup_and_unregister_flow(client):
    activity = "Chess Club"
    email = "pytest_user@example.com"

    # Ensure not present initially
    resp = client.get("/activities")
    assert resp.status_code == 200
    participants = resp.json()[activity]["participants"]
    if email in participants:
        # cleanup if a previous test left state
        client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")

    # Sign up
    resp = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Check participant is present
    resp = client.get("/activities")
    assert resp.status_code == 200
    participants = resp.json()[activity]["participants"]
    assert email in participants

    # Unregister
    resp = client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Verify removed
    resp = client.get("/activities")
    participants = resp.json()[activity]["participants"]
    assert email not in participants


def test_signup_duplicate_returns_400(client):
    activity = "Chess Club"
    email = "duplicate_test@example.com"

    # Ensure clean state
    client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")

    # First signup OK
    r1 = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
    assert r1.status_code == 200

    # Second signup should fail
    r2 = client.post(f"/activities/{quote(activity)}/signup?email={quote(email)}")
    assert r2.status_code == 400

    # Cleanup
    client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")


def test_unregister_not_registered_returns_404(client):
    activity = "Chess Club"
    email = "not_registered@example.com"

    # Ensure not registered
    client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")

    resp = client.delete(f"/activities/{quote(activity)}/unregister?email={quote(email)}")
    assert resp.status_code == 404
    assert "not registered" in resp.json().get("detail", "").lower()

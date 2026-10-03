import base64
import io

import pytest

from backend import create_app


PROFILE = {
    "name": "Test User", "age": 24, "sex": "female", "height_cm": 165,
    "weight_kg": 62, "activity_level": "moderate", "dietary_preference": "vegetarian",
    "goal": "balanced", "allergies": [], "cuisines": ["Indian"],
    "budget_per_day": 350, "timeline_weeks": 8,
}
VALID_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


@pytest.fixture
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE_PATH": str(tmp_path / "test.sqlite3"),
        "UPLOAD_DIR": str(tmp_path / "uploads"),
    })
    return app.test_client()


def register(client, email="test@example.com", name="Test User"):
    response = client.post("/api/auth/register", json={"name": name, "email": email, "password": "password123"})
    assert response.status_code == 201
    return response.get_json()["user"]


def test_health_and_logged_out_state(client):
    assert client.get("/api/health").get_json()["status"] == "ok"
    body = client.get("/api/auth/me").get_json()
    assert body["authenticated"] is False
    assert client.get("/api/dashboard").status_code == 401


def test_register_login_logout_and_duplicate_email(client):
    register(client)
    assert client.post("/api/auth/register", json={"name": "Other", "email": "test@example.com", "password": "password123"}).status_code == 409
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"}).status_code == 200
    assert client.post("/api/auth/logout").get_json()["ok"] is True
    assert client.get("/api/dashboard").status_code == 401


def test_profile_targets_plan_intake_and_dashboard(client):
    register(client)
    assert client.put("/api/profile", json=PROFILE).status_code == 200
    targets = client.post("/api/targets", json={}).get_json()["targets"]
    assert targets["calories"] > 0
    plan_response = client.post("/api/plans", json={"targets": targets})
    assert plan_response.status_code == 201
    plan = plan_response.get_json()["plan"]
    assert plan["meals"]
    assert len(client.get("/api/plans").get_json()["plans"]) == 1
    intake = client.post("/api/intake", json={"food_id": "apple", "grams": 150})
    assert intake.status_code == 201
    assert client.get("/api/intake").get_json()["totals"]["kcal"] == 78
    dashboard = client.get("/api/dashboard").get_json()
    assert dashboard["profile"]["name"] == "Test User"
    assert dashboard["current_plan"]["id"] == plan["id"]
    assert dashboard["today"]["intake"]["kcal"] == 78
    assert client.delete(f"/api/intake/{intake.get_json()['entry']['id']}").status_code == 200


def test_validation_and_upload(client):
    register(client)
    invalid = client.put("/api/profile", json={**PROFILE, "age": 4})
    assert invalid.status_code == 400
    upload = client.post("/api/storage/profile-photo", data={"file": (io.BytesIO(b"not-an-image"), "avatar.txt", "text/plain")}, content_type="multipart/form-data")
    assert upload.status_code == 400
    spoofed = client.post("/api/storage/profile-photo", data={"file": (io.BytesIO(b"not-a-png"), "avatar.png", "image/png")}, content_type="multipart/form-data")
    assert spoofed.status_code == 400
    good = client.post("/api/storage/profile-photo", data={"file": (io.BytesIO(VALID_PNG), "avatar.png", "image/png")}, content_type="multipart/form-data")
    assert good.status_code == 201
    upload_id = good.get_json()["upload"]["id"]
    assert client.get(f"/api/storage/{upload_id}").status_code == 200


def test_cross_user_resources_are_not_readable_or_mutable(client):
    register(client, "owner@example.com", "Owner")
    client.put("/api/profile", json={**PROFILE, "name": "Owner"})
    plan = client.post("/api/plans", json={}).get_json()["plan"]
    intake_id = client.post("/api/intake", json={"food_id": "apple", "grams": 150}).get_json()["entry"]["id"]
    upload_id = client.post("/api/storage/profile-photo", data={"file": (io.BytesIO(VALID_PNG), "owner.png", "image/png")}, content_type="multipart/form-data").get_json()["upload"]["id"]

    client.post("/api/auth/logout")
    register(client, "other@example.com", "Other")
    assert client.get("/api/plans").get_json()["plans"] == []
    assert client.get(f"/api/plans/{plan['id']}").status_code == 404
    assert client.delete(f"/api/intake/{intake_id}").status_code == 404
    assert client.get(f"/api/storage/{upload_id}").status_code == 404

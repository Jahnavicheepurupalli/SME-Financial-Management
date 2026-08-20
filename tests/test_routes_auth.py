import pytest
from flask_jwt_extended import create_access_token

from backend.models.models import User
from backend.routes import auth as auth_module


@pytest.mark.parametrize(
    "password, valid",
    [
        ("short", False),
        ("lowercase1!", False),
        ("UPPERCASE1!", False),
        ("Lowercase!", False),
        ("Lowercase1", False),
        ("Valid@123", True),
    ],
)
def test_validate_password(password, valid):
    assert auth_module.validate_password(password) is valid


def test_signup_validation_duplicate_and_success(client):
    assert client.post("/api/auth/signup", json={}).status_code == 400
    assert client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "a@example.com", "password": "Valid@123", "confirm_password": "Other@123"},
    ).status_code == 400
    assert client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "a@example.com", "password": "weak"},
    ).status_code == 400
    response = client.post(
        "/api/auth/signup",
        json={"name": "Alice", "email": "a@example.com", "password": "Valid@123", "confirm_password": "Valid@123"},
    )
    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == "a@example.com"
    assert client.post(
        "/api/auth/signup",
        json={"name": "Alice", "email": "a@example.com", "password": "Valid@123"},
    ).status_code == 400


def test_login_success_failures_and_google_user(client, session_factory):
    assert client.post("/api/auth/login", json={}).status_code == 400
    assert client.post("/api/auth/login", json={"email": "none", "password": "Valid@123"}).status_code == 401
    client.post("/api/auth/signup", json={"name": "A", "email": "a@example.com", "password": "Valid@123"})
    response = client.post("/api/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert response.status_code == 401
    response = client.post("/api/auth/login", json={"email": "a@example.com", "password": "Valid@123"})
    assert response.status_code == 200
    assert response.get_json()["token"]
    db = session_factory()
    db.add(User(full_name="Google", email="g@example.com", password_hash=None))
    db.commit()
    db.close()
    assert client.post("/api/auth/login", json={"email": "g@example.com", "password": "x"}).status_code == 401


def test_forgot_password_reset_and_validation(client):
    client.post("/api/auth/signup", json={"name": "A", "email": "a@example.com", "password": "Valid@123"})
    assert client.post("/api/auth/forgot-password", json={}).status_code == 400
    assert client.post(
        "/api/auth/reset-password",
        json={"email": "a@example.com", "new_password": "Valid@123", "confirm_password": "Other@123"},
    ).status_code == 400
    assert client.post(
        "/api/auth/reset-password",
        json={"email": "a@example.com", "new_password": "weak", "confirm_password": "weak"},
    ).status_code == 400
    assert client.post(
        "/api/auth/forgot-password",
        json={"email": "missing@example.com", "new_password": "Valid@123", "confirm_password": "Valid@123"},
    ).status_code == 404
    assert client.post(
        "/api/auth/reset-password",
        json={"email": "a@example.com", "new_password": "New@4567", "confirm_password": "New@4567"},
    ).status_code == 200
    assert client.post("/api/auth/login", json={"email": "a@example.com", "password": "New@4567"}).status_code == 200


def test_profile_and_logout(client, auth_token, session_factory):
    assert client.get("/api/auth/profile").status_code == 401
    response = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {auth_token}"}).status_code == 200
    db = session_factory()
    user = db.query(User).filter(User.email == "test@example.com").first()
    db.delete(user)
    db.commit()
    db.close()
    assert client.get("/api/auth/profile", headers={"Authorization": f"Bearer {auth_token}"}).status_code == 404


def test_google_route_is_unavailable_without_dependency_or_configuration(client, monkeypatch):
    pytest.importorskip("google.oauth2.id_token")
    monkeypatch.setattr(auth_module.Config, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(auth_module.Config, "GOOGLE_CLIENT_SECRET", None)
    assert client.post("/api/auth/google", json={}).status_code == 401

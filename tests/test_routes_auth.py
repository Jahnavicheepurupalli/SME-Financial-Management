import pytest

from backend.models.models import User
from backend.config import Config
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


def test_signup_missing_fields(client):
    assert client.post("/api/auth/signup", json={}).status_code == 400


def test_signup_password_mismatch(client):
    assert client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "a@example.com", "password": "Valid@123", "confirm_password": "Other@123"},
    ).status_code == 400


def test_signup_weak_password(client):
    assert client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "a@example.com", "password": "weak"},
    ).status_code == 400


def test_signup_success(client):
    response = client.post(
        "/api/auth/signup",
        json={"name": "Alice", "email": "a@example.com", "password": "Valid@123", "confirm_password": "Valid@123"},
    )
    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == "a@example.com"


def test_signup_duplicate_email(client):
    payload = {"name": "Alice", "email": "a@example.com", "password": "Valid@123"}
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    assert client.post(
        "/api/auth/signup",
        json=payload,
    ).status_code == 400


def test_login_success_failures_and_google_user(client, session_factory):
    assert client.post("/api/auth/login", json={}).status_code == 400
    assert client.post("/api/auth/login", json={"email": "none@example.com", "password": "Valid@123"}).status_code == 401
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


def test_forgot_password_and_reset_are_unavailable(client, session_factory):
    client.post("/api/auth/signup", json={"name": "A", "email": "a@example.com", "password": "Valid@123"})
    db = session_factory()
    original_hash = db.query(User).filter(User.email == "a@example.com").first().password_hash
    db.close()

    for path in ("/api/auth/forgot-password", "/api/auth/reset-password"):
        response = client.post(
            path,
            json={"email": "a@example.com", "new_password": "Changed@123", "confirm_password": "Changed@123"},
        )
        assert response.status_code == 503
        assert "Self-service password reset is unavailable" in response.get_json()["message"]

    db = session_factory()
    assert db.query(User).filter(User.email == "a@example.com").first().password_hash == original_hash
    db.close()


def test_change_password_success_and_validation(client, auth_token, session_factory):
    response = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "current_password": "Valid@123",
            "new_password": "Changed@123",
            "confirm_password": "Changed@123",
        },
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Password changed successfully"
    assert client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Changed@123"},
    ).status_code == 200

    wrong_current = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "current_password": "Wrong@123",
            "new_password": "Changed2@123",
            "confirm_password": "Changed2@123",
        },
    )
    assert wrong_current.status_code == 401

    mismatch = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "current_password": "Changed@123",
            "new_password": "Changed2@123",
            "confirm_password": "Different@123",
        },
    )
    assert mismatch.status_code == 400

    weak = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "current_password": "Changed@123",
            "new_password": "weak",
            "confirm_password": "weak",
        },
    )
    assert weak.status_code == 400

    db = session_factory()
    google_user = User(full_name="Google", email="google-only@example.com", password_hash=None)
    db.add(google_user)
    db.commit()
    google_user_id = google_user.id
    db.close()
    from flask_jwt_extended import create_access_token
    with client.application.app_context():
        google_token = create_access_token(identity=str(google_user_id))
    google_only = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {google_token}"},
        json={
            "current_password": "Current@123",
            "new_password": "Changed@123",
            "confirm_password": "Changed@123",
        },
    )
    assert google_only.status_code == 400
    assert "Google-only accounts" in google_only.get_json()["message"]


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


def _configure_google(monkeypatch):
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", "client.apps.googleusercontent.com")
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_SECRET", "secret")


def test_google_missing_credential(client, monkeypatch):
    _configure_google(monkeypatch)
    assert client.post("/api/auth/google", json={}).status_code == 400


def test_google_unconfigured_client(client, monkeypatch):
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_SECRET", None)
    assert client.post("/api/auth/google", json={}).status_code == 401


@pytest.mark.parametrize(
    "error, expected",
    [
        ("audience mismatch", "temporarily unavailable"),
        ("unauthorized account", "not authorized for the current OAuth testing"),
        ("unrelated verification failure", "Unable to verify your Google account"),
    ],
)
@pytest.mark.parametrize("exception_type", [ValueError, RuntimeError])
def test_google_verification_errors(client, monkeypatch, error, expected, exception_type):
    _configure_google(monkeypatch)
    from google.oauth2 import id_token

    def fail(*args, **kwargs):
        raise exception_type(error)

    monkeypatch.setattr(id_token, "verify_oauth2_token", fail)
    response = client.post("/api/auth/google", json={"credential": "token"})
    assert response.status_code == 401
    assert expected in response.get_json()["message"]


def test_google_empty_email(client, monkeypatch):
    _configure_google(monkeypatch)
    from google.oauth2 import id_token
    monkeypatch.setattr(id_token, "verify_oauth2_token", lambda *args: {"email": "", "name": "No Email"})
    response = client.post("/api/auth/google", json={"credential": "token"})
    assert response.status_code == 401
    assert "Unable to verify" in response.get_json()["message"]


def test_google_creates_new_user(client, monkeypatch, session_factory):
    _configure_google(monkeypatch)
    from google.oauth2 import id_token
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda *args: {"email": "new@example.com", "name": "New Google User"},
    )
    response = client.post("/api/auth/google", json={"credential": "token"})
    assert response.status_code == 200
    assert response.get_json()["token"]
    db = session_factory()
    user = db.query(User).filter(User.email == "new@example.com").all()
    assert len(user) == 1
    db.close()


def test_google_reuses_existing_user(client, monkeypatch, session_factory):
    _configure_google(monkeypatch)
    db = session_factory()
    db.add(User(full_name="Existing", email="existing@example.com", password_hash=None))
    db.commit()
    user_id = db.query(User).filter(User.email == "existing@example.com").first().id
    db.close()
    from google.oauth2 import id_token
    monkeypatch.setattr(
        id_token,
        "verify_oauth2_token",
        lambda *args: {"email": "EXISTING@example.com", "name": "Updated Name"},
    )
    response = client.post("/api/auth/google", json={"credential": "token"})
    assert response.status_code == 200
    db = session_factory()
    assert db.query(User).filter(User.email == "existing@example.com").count() == 1
    assert db.query(User).filter(User.email == "existing@example.com").first().id == user_id
    db.close()


class _BrokenSession:
    def query(self, *args):
        raise RuntimeError("database unavailable")

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


@pytest.mark.parametrize(
    "path, payload",
    [
        (
            "/api/auth/signup",
            {"name": "A", "email": "a@example.com", "password": "Valid@123"},
        ),
        ("/api/auth/login", {"email": "a@example.com", "password": "Valid@123"}),
    ],
)
def test_auth_database_errors_return_500(client, monkeypatch, path, payload):
    broken = _BrokenSession()
    monkeypatch.setattr(auth_module, "SessionLocal", lambda: broken)
    response = client.post(path, json=payload)
    assert response.status_code == 500
    assert response.get_json()["message"] == "An unexpected server error occurred. Please try again."
    if path == "/api/auth/signup":
        assert broken.rolled_back is True

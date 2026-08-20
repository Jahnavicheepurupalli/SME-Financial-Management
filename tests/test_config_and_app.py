import importlib

import pytest


def test_validate_oauth_config(monkeypatch):
    from backend.config import Config

    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_SECRET", None)
    assert Config.validate_oauth_config() is False
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", "malformed-client-id")
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_SECRET", "secret")
    assert Config.validate_oauth_config() is False
    monkeypatch.setattr(Config, "GOOGLE_CLIENT_ID", "client.apps.googleusercontent.com")
    assert Config.validate_oauth_config() is True


def test_backend_app_health_routes():
    backend_app = importlib.import_module("backend.app")
    client = backend_app.app.test_client()
    assert client.get("/").get_json() == {
        "status": "success",
        "message": "Financial Document Intelligence API is running",
    }
    assert client.get("/api/health").get_json() == {"status": "healthy", "backend": "running"}

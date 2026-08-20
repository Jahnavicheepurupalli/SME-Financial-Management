import os

import pytest
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def app(tmp_path, monkeypatch):
    from backend.database.db import Base
    from backend.routes import auth as auth_module
    from backend.routes import document as document_module
    from backend.agents import agent as agent_module
    from backend.config import Config

    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    monkeypatch.setattr(auth_module, "SessionLocal", session_factory)
    monkeypatch.setattr(document_module, "SessionLocal", session_factory)
    monkeypatch.setattr(agent_module, "SessionLocal", session_factory)
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
    monkeypatch.setattr(Config, "REPORTS_FOLDER", str(tmp_path / "reports"))
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)

    application = Flask(__name__)
    application.config.update(
        TESTING=True,
        JWT_SECRET_KEY="test-secret-key-with-at-least-32-bytes",
        MAX_CONTENT_LENGTH=20 * 1024 * 1024,
    )
    JWTManager(application)
    auth_module.bcrypt.init_app(application)
    application.register_blueprint(auth_module.auth_bp, url_prefix="/api/auth")
    application.register_blueprint(document_module.doc_bp, url_prefix="/api")
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session_factory(app, tmp_path):
    from backend.routes import auth as auth_module
    return auth_module.SessionLocal


@pytest.fixture
def auth_token(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "Valid@123",
            "confirm_password": "Valid@123",
        },
    )
    assert response.status_code == 201
    return client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Valid@123"},
    ).get_json()["token"]

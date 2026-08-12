"""Fixtures building the real site: the shipped config file, all apps installed.

`config_path` points at the repository's own `config/app.toml`, so the tests
exercise the configuration that ships rather than a parallel copy of it.
"""

from pathlib import Path

import pytest

from holdenweb import create_app
from podpack import db

CONFIG = Path(__file__).parents[1] / "config" / "app.toml"


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("SECURITY_PASSWORD_SALT", "test-password-salt")
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAIL_BACKEND": "dummy",
        },
        config_path=CONFIG,
        data_root=tmp_path / "data",
        log_root=tmp_path / "logs",
    )
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

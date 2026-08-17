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
def operator_app(monkeypatch, tmp_path):
    """The site as an operator sees it.

    `/_status` reports the database identity and every host path, so it
    answers only a member of the `admin` role. Standing one up in a test
    would mean a login round-trip; asserting the guard is a separate test,
    and this one is about what the report contains.
    """
    yield from _build(monkeypatch, tmp_path, admin=lambda: True)


@pytest.fixture
def app(monkeypatch, tmp_path):
    yield from _build(monkeypatch, tmp_path)


def _build(monkeypatch, tmp_path, **overrides):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("SECURITY_PASSWORD_SALT", "test-password-salt")
    # `[site] secrets` names this one, so podpack requires it at boot. It used
    # to arrive without being asked for: `load_dotenv()` in the package pulled
    # it out of a developer's `.env`, and the suite passed because of a file it
    # never mentions and CI would not have. Supplied here instead.
    monkeypatch.setenv("MAIL_PASSWORD", "test-mail-password")
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "MAIL_BACKEND": "dummy",
        },
        config_path=CONFIG,
        data_root=tmp_path / "data",
        log_root=tmp_path / "logs",
        **overrides,
    )
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

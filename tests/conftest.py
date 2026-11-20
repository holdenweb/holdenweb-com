"""Fixtures building the real site: the shipped config file, all apps installed.

`config_path` points at the repository's own `config/app.toml`, so the tests
exercise the configuration that ships rather than a parallel copy of it.
"""

from pathlib import Path
from typing import Any

import pytest
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from holdenweb import create_app
from podpack import db

CONFIG = Path(__file__).parents[1] / "config" / "app.toml"


class OwnContextClient(FlaskClient):
    """Each request in an app context of its own, as on a real server.

    `_build` below yields from inside `app.app_context()`, so that fixtures and
    tests can reach the database directly. But Flask reuses an app context
    already pushed for the same app instead of pushing one per request, so
    without this `g` would outlive every request, and with it what
    flask-login and flask-principal keep there (`_login_user`, `identity`).
    Measured: after a successful login through the form, the next request was
    refused "You must sign in" with `_user_id` still in the session. The same
    client and session in a fresh context got 200.

    Installed as every test app's client class, not offered as a fixture to
    ask for, because the trap is silent: a signed-in test written without
    knowing about it passes or fails for reasons the site never sees.
    """

    def open(self, *args: Any, **kwargs: Any) -> TestResponse:
        with self.application.app_context():
            return super().open(*args, **kwargs)


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
    # podpack-mail declares this one, so podpack requires it at boot. It used
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
    app.test_client_class = OwnContextClient
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

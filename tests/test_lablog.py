"""lablog on this site: SEC-1 holds for it.

Sign-up here is public, so a confirmed account is something any stranger can
have. SEC-1's guarantee is that such an account reaches nothing an anonymous
visitor does not, bar its own name in the nav. lablog keeps it with its own
`lablog` role: a signed-in user without the role gets 404 on every page, as
podpack's `operator_required` gives, and a 404 rather than a 403, so the
answer does not even confirm the app is there.

Here rather than in tests/integration because seeing that 404 needs a session,
and that suite carries no credential (HW-0029). This one makes its own users,
in its own throwaway database, with `test-` passwords. What the deployment
shows from outside, the gate and the missing nav entry, is
test_the_lablog_app_is_installed_and_closed_to_visitors.
"""

from datetime import datetime, timezone
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_security import hash_password
from werkzeug.test import TestResponse

from podpack import db
from podpack.auth import user_datastore

HOLDER = "holder@example.com"
STRANGER = "stranger@example.com"
PASSWORD = "test-password"
PROJECT = "Podpack PDF"
SLUG = "podpack-pdf"


@pytest.fixture
def people(app: Flask) -> None:
    """A holder of the `lablog` role and a confirmed stranger without it.

    Confirmed, because SECURITY_CONFIRMABLE is on and an unconfirmed account
    cannot sign in at all, which would make every 404 below pass for the
    wrong reason. The deliverability check goes for the same reason it does in
    test_password_reset.py: example.com has no MX record, and the login form
    looks.
    """
    app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}
    for email in (HOLDER, STRANGER):
        user_datastore.create_user(
            email=email,
            password=hash_password(PASSWORD),
            active=True,
            confirmed_at=datetime.now(timezone.utc),
        )
    db.session.commit()
    user_datastore.add_role_to_user(
        user_datastore.find_user(email=HOLDER), user_datastore.find_or_create_role("lablog")
    )
    db.session.commit()


class OwnContextClient(FlaskClient):
    """Each request in an app context of its own, as on a real server.

    conftest's `app` yields from inside `app.app_context()`, and Flask reuses
    an app context already pushed for the same app rather than pushing one per
    request. So `g` outlives the request, and with it what flask-login and
    flask-principal keep there (`_login_user`, `identity`). Measured: after a
    successful login through the form, the next request was refused "You must
    sign in" while the session still held `_user_id`; the same client and
    session, in a fresh context, got 200. Any signed-in test against that
    fixture needs this, or it passes and fails for reasons the site never sees.
    """

    def open(self, *args: Any, **kwargs: Any) -> TestResponse:
        with self.application.app_context():
            return super().open(*args, **kwargs)


def signed_in(app: Flask, email: str) -> FlaskClient:
    """A client holding a real session, obtained through the login form.

    The session is inspected rather than the status code, because a refused
    login also answers 200.
    """
    client = OwnContextClient(app, app.response_class, use_cookies=True)
    client.post("/login", data={"email": email, "password": PASSWORD}, follow_redirects=True)
    with client.session_transaction() as session:
        assert "_user_id" in session, f"signing in as {email} did not take"
    return client


@pytest.fixture
def holder(app: Flask, people: None) -> FlaskClient:
    client = signed_in(app, HOLDER)
    # A project and an experiment, so the stranger is refused things that
    # exist, not only things that do not.
    client.post("/lablog/new", data={"name": PROJECT, "description": ""})
    client.post(
        f"/lablog/{SLUG}/experiments/new",
        data={"title": "Booklets", "expectation": "Pages come out in booklet order."},
    )
    return client


@pytest.fixture
def stranger(app: Flask, people: None) -> FlaskClient:
    return signed_in(app, STRANGER)


PAGES = [
    "/lablog/",
    "/lablog/new",
    f"/lablog/{SLUG}/",
    f"/lablog/{SLUG}/edit",
    f"/lablog/{SLUG}/experiments/new",
    f"/lablog/{SLUG}/experiments/1",
]


@pytest.mark.parametrize("path", PAGES)
def test_a_role_holder_reaches_every_page(holder: FlaskClient, path: str) -> None:
    """The other half of the stranger's 404s: the same pages, the same site,
    answering 200 to the role. Without it, 404s everywhere would pass just as
    well for an app that never mounted."""
    assert holder.get(path).status_code == 200


@pytest.mark.parametrize("path", PAGES + ["/lablog/no-such-project/"])
def test_a_confirmed_stranger_gets_404_everywhere(
    holder: FlaskClient, stranger: FlaskClient, path: str
) -> None:
    """Existing project, missing project: the same 404, so a stranger cannot
    tell which projects exist."""
    assert stranger.get(path).status_code == 404


def test_a_confirmed_stranger_cannot_write(holder: FlaskClient, stranger: FlaskClient) -> None:
    """Refused before the form is read, and nothing recorded."""
    response = stranger.post(
        f"/lablog/{SLUG}/experiments/1/entries",
        data={"kind": "observation", "body": "I was here.", "corrects": "0"},
    )
    assert response.status_code == 404
    assert "I was here." not in holder.get(f"/lablog/{SLUG}/experiments/1").get_data(as_text=True)


def test_an_anonymous_visitor_is_sent_to_log_in(client: FlaskClient) -> None:
    response = client.get("/lablog/")
    assert response.status_code == 302
    assert response.headers["Location"].startswith("/login?next=")

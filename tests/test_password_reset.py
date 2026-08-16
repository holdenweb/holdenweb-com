"""What a password reset does when the mail will not go.

The site spent a while with a dead SMTP credential, and `POST /reset`
answered 500 with a traceback: flask-security calls `send_mail` from inside
`forgot_password` and catches nothing the backend raises. These pin the
behaviour that replaced it.
"""

import pytest
from flask_security import hash_password

from holdenweb.models import user_datastore
from podpack import db

BROKEN = "smtplib.SMTPAuthenticationError(535, b'5.7.8 Username and Password not accepted')"


@pytest.fixture
def registered(app):
    """A user who exists, because `send_mail` is only reached for one.

    The deliverability check goes with them. flask-security validates the
    address on the way in through `email_validator`, which by default resolves
    MX records -- and `example.com`, being reserved for documentation, has
    none. Left on, the form fails with "Invalid email address", the view never
    reaches `send_mail`, and every test here passes for the wrong reason.
    """
    app.config["SECURITY_EMAIL_VALIDATOR_ARGS"] = {"check_deliverability": False}
    with app.app_context():
        user_datastore.create_user(
            email="someone@example.com", password=hash_password("x" * 12), active=True
        )
        db.session.commit()
    return "someone@example.com"


@pytest.fixture
def mail_is_broken(monkeypatch):
    """Make delivery fail the way a rejected credential does.

    Patched at flask-security's own `MailUtil.send_mail` -- which is exactly
    what `ReportingMailUtil` calls through to -- so the failure arrives from
    where a real backend failure would.
    """
    from flask_security.mail_util import MailUtil

    def refuse(*args, **kwargs):
        raise OSError("[Errno 61] Connection refused")

    monkeypatch.setattr(MailUtil, "send_mail", refuse)


def test_a_dead_mail_server_is_not_a_500(client, registered, mail_is_broken):
    """The whole point. A service problem the visitor cannot act on must not
    be handed to them as a traceback."""
    response = client.post("/reset", data={"email": registered})
    assert response.status_code != 500


def test_the_visitor_is_told_the_mail_failed(client, registered, mail_is_broken):
    """flask-security flashes its own "instructions have been sent" whatever
    happens, so without this somebody waits for an email that never left."""
    response = client.post("/reset", data={"email": registered}, follow_redirects=True)
    assert b"could not be sent" in response.data


def test_the_failure_reaches_the_log(app, client, registered, mail_is_broken, caplog):
    """The operator's half: the visitor gets a sentence, the log gets the cause."""
    with caplog.at_level("ERROR"):
        client.post("/reset", data={"email": registered})
    assert "could not send" in caplog.text
    assert "OSError" in caplog.text


def test_generic_responses_keep_the_failure_quiet(
    app, client, registered, mail_is_broken
):
    """`send_mail` is only reached for an address that has an account, so the
    message would otherwise distinguish a registered address from an
    unregistered one -- the one thing this setting exists to prevent."""
    app.config["SECURITY_RETURN_GENERIC_RESPONSES"] = True
    response = client.post("/reset", data={"email": registered}, follow_redirects=True)
    assert response.status_code != 500
    assert b"could not be sent" not in response.data


def test_a_working_send_says_nothing_about_failure(client, registered):
    """The control: with the dummy backend the tests use, nothing goes wrong
    and no apology is offered."""
    response = client.post("/reset", data={"email": registered}, follow_redirects=True)
    assert response.status_code != 500
    assert b"could not be sent" not in response.data

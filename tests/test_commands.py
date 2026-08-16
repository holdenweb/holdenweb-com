"""`flask mail check`, which exists so that "is the mail credential good?" has
a direct answer rather than being inferred from a password-reset round trip."""

import pytest
from flask_security.mail_util import MailUtil


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def mail_is_broken(monkeypatch):
    """Refuse the connection the way an unreachable or rejecting server does.

    Patched at `get_connection`, which is what the command calls, rather than
    inside a backend: the tests run on the dummy backend, whose `open` never
    contacts anything and so cannot be made to fail from within.

    `_MailMixin` and not `Mail`, because `app.extensions["mailman"]` is a
    `_Mail` -- a sibling rather than a subclass, and the two share only that
    mixin. Patching `Mail` looks right, changes nothing, and leaves the test
    passing against unmodified code.
    """
    class Refusing:
        def open(self) -> None:
            raise OSError("[Errno 61] Connection refused")

        def close(self) -> None:
            pass

    monkeypatch.setattr(
        "flask_mailman._MailMixin.get_connection", lambda self, *a, **k: Refusing()
    )


def test_a_working_server_reports_ok(runner, monkeypatch):
    monkeypatch.setattr(MailUtil, "send_mail", lambda *a, **k: None)
    result = runner.invoke(args=["mail", "check"])
    assert result.exit_code == 0
    assert "SMTP auth OK" in result.output


def test_a_refused_connection_exits_non_zero(runner, mail_is_broken):
    """So a deployment step can gate on it rather than reading the output."""
    result = runner.invoke(args=["mail", "check"])
    assert result.exit_code == 1
    assert "SMTP auth FAILED" in result.output


def test_it_reports_the_username_too(runner, monkeypatch):
    """A correct password authenticating as the wrong account fails exactly
    like a wrong password, so the account has to be on screen beside it."""
    monkeypatch.setattr(MailUtil, "send_mail", lambda *a, **k: None)
    result = runner.invoke(args=["mail", "check"])
    assert "steve@holdenweb.com" in result.output


def test_an_app_password_is_recognised(app, runner, monkeypatch):
    monkeypatch.setattr(MailUtil, "send_mail", lambda *a, **k: None)
    app.config["MAIL_PASSWORD"] = "abcdefghijklmnop"          # 16 lowercase
    result = runner.invoke(args=["mail", "check"])
    assert "shape matches a Google App Password" in result.output


def test_the_wrong_kind_of_password_is_called_out(app, runner, monkeypatch):
    """The actual mistake this was written for: a generated passphrase from
    Google's Password Manager rather than an App Password."""
    monkeypatch.setattr(MailUtil, "send_mail", lambda *a, **k: None)
    app.config["MAIL_PASSWORD"] = "cor-rect-horse-bat-tery-staple"
    result = runner.invoke(args=["mail", "check"])
    assert "NOT the shape of a Google App Password" in result.output


def test_gmails_display_spaces_are_flagged(app, runner, monkeypatch):
    """Google shows an App Password as four groups of four; pasted verbatim
    the spaces come too, and Gmail rejects it."""
    monkeypatch.setattr(MailUtil, "send_mail", lambda *a, **k: None)
    app.config["MAIL_PASSWORD"] = "abcd efgh ijkl mnop"
    result = runner.invoke(args=["mail", "check"])
    assert "spaces present" in result.output
    # Still recognisably the right secret, just pasted carelessly.
    assert "shape matches a Google App Password" in result.output


def test_the_password_itself_is_never_printed(app, runner, monkeypatch):
    monkeypatch.setattr(MailUtil, "send_mail", lambda *a, **k: None)
    app.config["MAIL_PASSWORD"] = "sup3rs3cr3tvalue"
    result = runner.invoke(args=["mail", "check"])
    assert "sup3rs3cr3tvalue" not in result.output

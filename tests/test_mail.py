"""Mail is the podpack-mail app's (HW-0037): what this site's config hands it.

Read back off a booted site rather than from the source, because a setting is
believed only once it has been read there -- `_wire` once said 'strict' while
the running site served SameSite=None (podpack briefing, §6).
"""

from pathlib import Path

import pytest

from holdenweb import create_app
from holdenweb.mail_util import ReportingMailUtil

CONFIG = Path(__file__).parents[1] / "config" / "app.toml"


@pytest.fixture
def deployed(monkeypatch, tmp_path):
    """The site as a deployment builds it: not a laptop, so mail goes by SMTP,
    with the login and the address a deployment's .env supplies.

    Built and inspected only. Nothing here opens a connection, so the real
    server named in config/app.toml is never contacted.
    """
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setenv("SECURITY_PASSWORD_SALT", "test-password-salt")
    monkeypatch.setenv("MAIL_PASSWORD", "test-mail-password")
    monkeypatch.setenv("MAIL_USERNAME", "test-login")
    monkeypatch.setenv("MAIL_ADDRESS", "test-stag@example.test")
    monkeypatch.setenv("PODPACK_ENVIRONMENT", "production")
    monkeypatch.delenv("MAIL_BACKEND", raising=False)
    return create_app(config_path=CONFIG, data_root=tmp_path / "data", log_root=tmp_path / "logs")


def test_mail_goes_to_opalstack_over_implicit_tls(deployed):
    config = deployed.config
    assert config["MAIL_BACKEND"] == "smtp"
    assert (config["MAIL_SERVER"], config["MAIL_PORT"]) == ("smtp.de.opalstack.com", 465)
    assert (config["MAIL_USE_SSL"], config["MAIL_USE_TLS"]) == (True, False)
    assert config["MAIL_USERNAME"] == "test-login"


def test_password_resets_leave_from_the_deployment_address(deployed):
    """Not steve@holdenweb.com, which `_wire` used to pin and which would still
    win if anything here set the sender before podpack-mail installs."""
    with deployed.app_context():
        assert str(deployed.config["SECURITY_EMAIL_SENDER"]) == (
            "Holden Web <test-stag@example.test>"
        )


def test_what_a_failure_says_is_still_the_sites(deployed):
    assert deployed.config["PODPACK_MAIL_UTIL_CLS"] is ReportingMailUtil


def test_mail_check_is_still_where_operations_md_says(deployed):
    result = deployed.test_cli_runner().invoke(args=["mail", "--help"])
    assert result.exit_code == 0, result.output
    assert "check" in result.output

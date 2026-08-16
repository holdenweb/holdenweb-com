"""The site's management commands.

A Flask command rather than a file under `scripts/`, on podpack's own
distinction (ADR-0031): *what needs no running application is a script, and
anything that needs one is a Flask command*. Checking the mail credential
needs the application -- its config, and the mail extension the site wired --
so it belongs here.

That is not only tidiness. `scripts/` is deliberately not copied into the
image, so a check living there could only be piped into a container from
outside. `src/` is copied, so this runs where the problem actually is:

    podman compose exec web flask --app holdenweb mail check
"""

import click
from flask import current_app
from flask.cli import with_appcontext

APP_PASSWORD_LENGTH = 16
"""What Google issues, once the spaces of its four-by-four display are gone."""


@click.group("mail")
def mail_commands() -> None:
    """Mail commands."""


@mail_commands.command("check")
@with_appcontext
def check() -> None:
    """Authenticate against the mail server, and do nothing else.

    Written after an afternoon spent deciding whether a rejected Gmail App
    Password was the password, the username, the wrong file, or the site --
    a question a password-reset round trip answers slowly, because a failure
    there could be any of them.

    Reports what the connection would use as well as the outcome, since a
    correct password authenticating as the wrong account fails identically to
    a wrong one. Exits non-zero on failure, so a deployment step can gate on
    it. The password is never printed.
    """
    config = current_app.config
    click.echo("mail configuration:")
    click.echo(
        f"  server    : {config.get('MAIL_SERVER')}:{config.get('MAIL_PORT')}"
        f"  SSL={config.get('MAIL_USE_SSL')}  TLS={config.get('MAIL_USE_TLS')}"
    )
    click.echo(f"  username  : {config.get('MAIL_USERNAME')}")
    click.echo(f"  password  : {_describe_password(config.get('MAIL_PASSWORD'))}")

    connection = current_app.extensions["mailman"].get_connection()
    try:
        connection.open()
    except Exception as exc:  # noqa: BLE001 -- every backend raises its own family
        click.echo(f"\nSMTP auth FAILED: {type(exc).__name__}", err=True)
        click.echo(f"  {exc}", err=True)
        raise SystemExit(1) from exc
    connection.close()
    click.echo("\nSMTP auth OK")


def _describe_password(password: str | None) -> str:
    """Say enough to spot the usual mistake, and no more than that.

    The mistake being a perfectly good password taken from the wrong page of
    Google's security site: App Passwords live under 2-Step Verification,
    while passwords.google.com holds saved site logins, whose generated
    passphrases are longer and hyphenated.
    """
    if not password:
        return "NOT SET"
    stripped = password.replace(" ", "")
    spaces = " (spaces present, which Gmail does not want)" if " " in password else ""
    shape = (
        "shape matches a Google App Password"
        if len(stripped) == APP_PASSWORD_LENGTH and stripped.isalpha() and stripped.islower()
        else f"NOT the shape of a Google App Password, which is "
        f"{APP_PASSWORD_LENGTH} lowercase letters"
    )
    return f"{len(password)} characters{spaces}\n              {shape}"

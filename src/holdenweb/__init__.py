"""holdenweb.com: a podpack site.

podpack supplies the factory, the app registry, the migration wiring and --
since ADR-0033 -- login. This package supplies the site's chrome
(`templates/`, `static/`), its own routes (`views.py`, installed as the app
named `main`), and the wiring for the extensions that are still the site's:
mail and session policy. The installed-app list lives in `config/app.toml`.
"""

import os
from logging import basicConfig, getLogger

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_mailman import Mail
from flask_paranoid import Paranoid

import podpack

from .commands import mail_commands
from .mail_util import ReportingMailUtil

# The registry looks for `site_app` at module level: this package is itself an
# installed app -- the first name in `[site] apps` -- carrying the site's own
# routes and nav.
from .views import site_app  # noqa: F401

load_dotenv()

basicConfig(format='%(filename)s: %(levelname)s: %(message)s')
logger = getLogger(__name__)

# Extensions are created unbound and attached to an app in _wire(), so
# multiple app instances (e.g. one per test) can coexist safely. Login is not
# among them any more: podpack installs flask-security itself, including the
# models, the datastore and the `admin` predicate this file used to supply.
mail = Mail()
paranoid = Paranoid()


def create_app(config_overrides=None, **podpack_kwargs):
    """Application factory.

    `config_overrides` lets callers (tests, alternate entry points) replace
    config values without touching the environment; `podpack_kwargs` passes
    podpack's test entry points (`host_config`, `config_path`, `data_root`,
    `log_root`) through for the same reason.
    """
    return podpack.create_app(
        config_overrides,
        site_package="holdenweb",
        init=_wire,
        **podpack_kwargs,
    )


def _wire(app: Flask) -> None:
    """The site's own extensions: mail and session policy.

    podpack has already loaded the host config and applied `config_overrides`
    by the time this runs, so every setting here is a `setdefault` -- an
    override from a caller wins over the environment and these constants.
    """
    app.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    # SECURITY_PASSWORD_SALT used to be here too. podpack requires it now and
    # reads it itself, failing at boot if it is missing rather than letting the
    # site start and die inside `flask users create`.
    app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD'))

    # Public sign-up, gated by email confirmation. SECURITY_CONFIRMABLE means a
    # registrant gets no session until they follow a link mailed to the address
    # they gave, so registration cannot hand a bot or a stranger an instant
    # authenticated account -- which, with confirmation off, it once did, and
    # which was half of SEC-1's finding. The other half -- that such an account
    # could then read /config -- is closed independently: /config and /_status
    # answer only the admin predicate, and a confirmed non-admin reaches nothing
    # an anonymous visitor does not, bar its own name in the nav.
    # SECURITY_RECOVERABLE lets anyone reset their own password.
    app.config.setdefault('SECURITY_REGISTERABLE', True)
    app.config.setdefault('SECURITY_CONFIRMABLE', True)
    app.config.setdefault('SECURITY_RECOVERABLE', True)
    app.config.setdefault('REMEMBER_COOKIE_SAMESITE', 'strict')
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'strict')

    for key in ('MAIL_USERNAME', 'MAIL_DEFAULT_SENDER', 'SECURITY_EMAIL_SENDER'):
        app.config.setdefault(key, 'steve@holdenweb.com')
    app.config.setdefault('MAIL_SERVER', 'smtp.gmail.com')
    app.config.setdefault('MAIL_PORT', 465)
    app.config.setdefault('MAIL_USE_TLS', False)
    app.config.setdefault('MAIL_USE_SSL', True)
    app.config.setdefault('MAIL_BACKEND', 'smtp')

    # podpack installs flask-security after this function returns, and passes
    # this class through to it. Set here rather than there because what happens
    # when a message cannot be sent is the site's business: podpack neither
    # knows nor cares which mail server this is.
    app.config.setdefault('PODPACK_MAIL_UTIL_CLS', ReportingMailUtil)

    paranoid.init_app(app)
    paranoid.redirect_view = '/'

    mail.init_app(app)

    app.register_error_handler(404, _handle_404)
    # `flask --app holdenweb mail check`, alongside flask-security's own
    # `users` and `roles` groups. See commands.py for why it is a command
    # rather than a file under scripts/.
    app.cli.add_command(mail_commands)


def _handle_404(e):
    return render_template("404.html", title="Page not found", content=e), 404

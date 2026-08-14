"""holdenweb.com: a podpack site.

podpack supplies the factory, the app registry and the migration wiring; this
package supplies the site's chrome (`templates/`, `static/`), its own routes
(`views.py`, installed as the app named `main`), and the wiring for the
extensions that belong to the site rather than to any feature -- mail, login,
session policy. The installed-app list lives in `config/app.toml`.
"""

import os
from logging import basicConfig, getLogger

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_mailman import Mail
from flask_paranoid import Paranoid
from flask_security import Security, current_user

import podpack

from .models import user_datastore

# The registry looks for `site_app` at module level: this package is itself an
# installed app -- the first name in `[site] apps` -- carrying the site's own
# routes and nav.
from .views import site_app  # noqa: F401

load_dotenv()

basicConfig(format='%(filename)s: %(levelname)s: %(message)s')
logger = getLogger(__name__)

# Extensions are created unbound and attached to an app in _wire(), so
# multiple app instances (e.g. one per test) can coexist safely.
mail = Mail()
paranoid = Paranoid()
security = Security()


def create_app(config_overrides=None, **podpack_kwargs):
    """Application factory.

    `config_overrides` lets callers (tests, alternate entry points) replace
    config values without touching the environment; `podpack_kwargs` passes
    podpack's test entry points (`host_config`, `config_path`, `data_root`,
    `log_root`) through for the same reason.
    """
    # setdefault rather than a fixed argument, so a caller (a test, an
    # alternate entry point) can supply its own operator predicate.
    podpack_kwargs.setdefault("admin", _is_admin)
    return podpack.create_app(
        config_overrides,
        site_package="holdenweb",
        init=_wire,
        **podpack_kwargs,
    )


def _is_admin() -> bool:
    """Who may read `/_status`, which reports this site's own configuration.

    podpack has no login of its own, so it asks the site. Membership of the
    `admin` role, not merely being signed in: the report names the database,
    the role it connects as and every host path, which is operator business
    rather than user business.

    The role has to exist and be granted before anyone qualifies -- a fresh
    database has neither, so `/_status` answers 404 until somebody sets that
    up, which is the right way round.
    """
    return bool(current_user.is_authenticated and current_user.has_role("admin"))


def _wire(app: Flask) -> None:
    """The site's own extensions: mail, login, session policy.

    podpack has already loaded the host config and applied `config_overrides`
    by the time this runs, so every setting here is a `setdefault` -- an
    override from a caller wins over the environment and these constants.
    """
    app.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    for key in ('SECURITY_PASSWORD_SALT', 'MAIL_PASSWORD'):
        app.config.setdefault(key, os.environ.get(key))

    app.config.setdefault('SECURITY_REGISTERABLE', True)
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

    paranoid.init_app(app)
    paranoid.redirect_view = '/'

    mail.init_app(app)
    security.init_app(app, user_datastore)

    app.register_error_handler(404, _handle_404)


def _handle_404(e):
    return render_template("404.html", title="Page not found", content=e), 404

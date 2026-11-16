"""holdenweb.com: a podpack site.

podpack supplies the factory, the app registry, the migration wiring and --
since ADR-0033 -- login. This package supplies the site's chrome
(`templates/`, `static/`), its own routes (`views.py`, installed as the app
named `main`), and the wiring that is still the site's: session policy, and
what a mail failure says. Mail itself is the podpack-mail app (HW-0037). The
installed-app list lives in `config/app.toml`.
"""

import os
from logging import basicConfig, getLogger

from dotenv import load_dotenv
from flask import Flask, render_template

import podpack
from podpack.proxy import LOCAL, deployment_environment

from .mail_util import ReportingMailUtil

# The registry looks for `site_app` at module level: this package is itself an
# installed app -- the first name in `[site] apps` -- carrying the site's own
# routes and nav.
from .views import site_app  # noqa: F401

load_dotenv()

basicConfig(format='%(filename)s: %(levelname)s: %(message)s')
logger = getLogger(__name__)

# No extension is created here any more. podpack installs flask-security
# itself, including the models, the datastore and the `admin` predicate this
# file used to supply, and mail is the podpack-mail app's (HW-0037).


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
    """The site's own wiring: session policy, and what a mail failure says.

    podpack has already loaded the host config and applied `config_overrides`
    by the time this runs, so a setting here is a `setdefault` -- an override
    from a caller wins over the environment and these constants.

    The cookie policy is the exception, and assigns. A key Flask ships in its
    own defaults is already present by the time this runs, so `setdefault`
    finds it and does nothing; those keys can be set but not defaulted.
    """
    app.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    # Neither SECURITY_PASSWORD_SALT nor MAIL_PASSWORD is read here any more.
    # podpack requires the salt and reads it itself; the mail password belongs
    # to podpack-mail, which declares it. Both now fail at boot rather than
    # inside the first command or request that needs them.

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

    # Cookie policy, and the one block here that assigns rather than defaults.
    # Flask ships SESSION_COOKIE_SAMESITE and SESSION_COOKIE_SECURE in its own
    # defaults, so the `setdefault` this replaces found the key present and did
    # nothing: the line read 'strict' while the running site served
    # SESSION_COOKIE_SAMESITE=None. REMEMBER_COOKIE_SAMESITE is not a Flask key,
    # so that one did take -- two adjacent lines, one live and one dead, which is
    # why they are now together and explicit.
    #
    # Secure follows the deployment rather than being hardcoded, for ADR-0039's
    # reason: a derived value cannot be forgotten and cannot drift from what it
    # describes. Hardcoding True would break the laptop, where the dev site
    # speaks plain HTTP -- the cookie would never be sent and login would fail
    # with nothing on screen to explain it.
    #
    # Lax, not Strict, for the session cookie: confirmation and password-reset
    # links arrive in mail, and Strict sends no cookie on a cross-site top-level
    # navigation. The remember cookie keeps the Strict it already had, whose
    # worst case is milder -- a visitor arriving from a mail link is simply not
    # remembered and logs in again.
    secure_cookies = deployment_environment() != LOCAL
    app.config.update(
        SESSION_COOKIE_SECURE=secure_cookies,
        SESSION_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=secure_cookies,
        REMEMBER_COOKIE_SAMESITE='strict',
    )

    # Mail is podpack-mail's: server and sender name from [apps.mail], the login
    # and the address from the deployment's .env (HW-0037). Nothing here may set
    # MAIL_DEFAULT_SENDER or SECURITY_EMAIL_SENDER -- this runs before any app
    # installs, so a default set here would beat the deployment's own address,
    # and flask-security's sender already follows MAIL_DEFAULT_SENDER by itself.

    # podpack installs flask-security after this function returns, and passes
    # this class through to it. Set here rather than there because what happens
    # when a message cannot be sent is the site's business: podpack neither
    # knows nor cares which mail server this is.
    app.config.setdefault('PODPACK_MAIL_UTIL_CLS', ReportingMailUtil)

    app.register_error_handler(404, _handle_404)
    # `flask --app holdenweb mail check` still works: podpack-mail's blueprint
    # carries the `mail` group, which Flask registers under the app's name.


def _handle_404(e):
    return render_template("404.html", title="Page not found", content=e), 404

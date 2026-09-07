"""The site's own routes, packaged as its in-repo podpack app.

Content and QR codes moved out to `podpack-pages` and `podpack-qrcode`; what
stays here is the front page, the odd utility route, and permanent redirects
teaching the old content URLs their new addresses.
"""

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from podpack import Section, SiteApp

from .version import __version__

blueprint = Blueprint("main", __name__)


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


def site_map(app):
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append({
                "url": url,
                "rule": rule.endpoint,
            })
    return links


######## / ########
@blueprint.route("/")
def home_page():
    "Serve home page from index.html."
    return render_template("index.html")


######## /config ########
# Config keys whose *value* is a secret: any name carrying one of these markers,
# plus the database URI, whose name does not advertise the password embedded in
# it. Reported as shape, never value -- the house rule for secrets everywhere.
_SECRET_MARKERS = ("SECRET", "PASSWORD", "SALT", "TOKEN", "KEY")


def _redacted(key, value):
    name = key.upper()
    if name == "SQLALCHEMY_DATABASE_URI" or any(m in name for m in _SECRET_MARKERS):
        return f"<redacted, {len(str(value))} chars>"
    return str(value)


@blueprint.route("/config")
def get_version():
    # Operator-only, guarded exactly as podpack guards /_status: through the
    # site's configured admin predicate (ADR-0033), which defaults to
    # membership of the `admin` role. 404 rather than 403 to everyone else.
    # And the secret *values* are redacted below regardless -- SECRET_KEY, the
    # database URI, MAIL_PASSWORD and friends -- so a slip in that guard, of
    # which there has been one, cannot leak them: the guard defends the config's
    # shape, the redaction defends its secrets.
    admin = current_app.extensions["podpack"].admin
    try:
        allowed = admin is not None and admin()
    except Exception:  # noqa: BLE001 -- a broken guard denies, it does not admit
        allowed = False
    if not allowed:
        abort(404)
    return {
        "server_version": __version__,
        "site_map": site_map(current_app),
        "config": {k: _redacted(k, v) for (k, v) in current_app.config.items()},
    }


######## /ip ########
@blueprint.route("/ip", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200


######## /parts/xxxxxxx ########
@blueprint.route("/parts/<number>")
def parts_demo(number: str):
    if number != "demo":
        flash("Sorry, we only do demos at present!")
        abort(404)
    return redirect(url_for("pages.page", name="parts_demo"))


######## /python -> the pybooks app ########
# The Python course content now lives in the pybooks app at /pybooks (it moved
# out of the retired static tree, briefly through the pages app, and now stands
# as its own app). This is a permanent redirect for old /python bookmarks -- the
# nav's "Python" entry is pybooks' own now, not this route. Every old sub-path
# collapses onto the pybooks root; deep links that named a specific page are
# caught by the /pages/python-classes route below instead.
@blueprint.route("/python/", defaults={"path": ""})
@blueprint.route("/python/<path:path>")
def python_docs(path: str):
    return redirect(url_for("pybooks.page"), 301)


######## /pages/python-classes/... -> pybooks (old deep links) ########
# The course books moved out of the pages app into pybooks, so a bookmark to a
# page under /pages/python-classes follows to the same path under /pybooks. This
# has more static segments than the pages app's own /<path:name> catch-all, so
# Flask routes it here first -- a fact pinned by
# test_old_python_classes_urls_redirect_to_pybooks, since the route depends on
# exactly that precedence.
@blueprint.route("/pages/python-classes", defaults={"rest": ""})
@blueprint.route("/pages/python-classes/", defaults={"rest": ""})
@blueprint.route("/pages/python-classes/<path:rest>")
def legacy_python_classes(rest: str):
    return redirect(url_for("pybooks.page", name=rest), 301)


######## Legacy content URLs ########
# /note/, /page/ and /asset/ belong to the pages app now, which serves one
# name space instead of two. Old addresses are taught the new ones, so
# bookmarks and search engines follow.

@blueprint.route("/note/<name>")
def legacy_note(name: str):
    return redirect(url_for("pages.page", name=name), 301)


@blueprint.route("/page/<path:name>/")
def legacy_page(name: str):
    return redirect(url_for("pages.page", name=name), 301)


@blueprint.route("/asset/<path:path>")
def legacy_asset(path: str):
    # Old asset paths carried the tree name ("html/..." or "md/..."); the
    # unified space drops it.
    head, _, tail = path.partition("/")
    if head in ("html", "md") and tail:
        path = tail
    return redirect(url_for("pages.asset", path=path), 301)


site_app = SiteApp(
    blueprint=blueprint,
    url_prefix=None,          # the site root: the front page is this app's
    nav=(
        # "Python" is the pybooks app's nav entry now (podpack_pages.pybooks);
        # this app must not contribute it too, or the nav lists it twice.
        Section("Home", "main.home_page"),
    ),
    # No `owns_tables` any more: `user`, `role` and `roles_users` became
    # podpack's when login did (ADR-0033), and podpack records itself as their
    # owner. Claiming them here as well would be this app asserting ownership
    # of the framework's tables, which is the collision the field exists to
    # make visible rather than a use of it.
)

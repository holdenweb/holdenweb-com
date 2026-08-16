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
    send_from_directory,
    url_for,
)
from flask_security import auth_required

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
@blueprint.route("/config")
@auth_required('session')
def get_version():
    return {
        "server_version": __version__,
        "site_map": site_map(current_app),
        "config": {k: str(v) for (k, v) in current_app.config.items()}
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


######## /python ########
# The default lets url_for build the nav entry without arguments.
@blueprint.route("/python/", defaults={"path": "index.html"})
@blueprint.route("/python/<path:path>")
def python_docs(path: str):
    return send_from_directory("static/python/web", path)


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
        Section("Home", "main.home_page"),
        Section("Python", "main.python_docs"),
    ),
    # No `owns_tables` any more: `user`, `role` and `roles_users` became
    # podpack's when login did (ADR-0033), and podpack records itself as their
    # owner. Claiming them here as well would be this app asserting ownership
    # of the framework's tables, which is the collision the field exists to
    # make visible rather than a use of it.
)

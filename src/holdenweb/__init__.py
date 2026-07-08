import os
import io
import qrcode
import re

from dataclasses import dataclass
from importlib.resources import files
from logging import getLogger, basicConfig
from pathlib import Path

import markdown

from dotenv import load_dotenv
from flask import (
    abort,
    Blueprint,
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    url_for,
    send_from_directory,
)
from flask_mailman import Mail
from flask_paranoid import Paranoid
from flask_security import Security, SQLAlchemyUserDatastore, auth_required
from flask_security.models import fsqla_v3 as fsqla
from flask_sqlalchemy import SQLAlchemy

import holdenweb
from .content import (
    ContentNotFound,
    ContentUnavailable,
    HTTPContentSource,
    LocalContentSource,
    rewrite_asset_urls,
)
from .forms import QRcode_Form
from .pdf import pdf_blueprint
from .version import __version__

load_dotenv()

basicConfig(format='%(filename)s: %(levelname)s: %(message)s')
logger = getLogger(__name__)


@dataclass
class Section:
    label: str
    path: str

# Locate data directory inside site
DATA_PATH = files(holdenweb) / 'data'

# Define section URL
SECTIONS = [
    Section("Home", "/"),
    Section("Python", "/python"),
    Section("Blog", "/blog")
]

md = markdown.Markdown(extensions=['mdx_math', 'codehilite'])

# Extensions are created unbound and attached to an app in create_app(),
# so multiple app instances (e.g. one per test) can coexist safely.
mail = Mail()
paranoid = Paranoid()
db = SQLAlchemy()
security = Security()

fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    pass


user_datastore = SQLAlchemyUserDatastore(db, User, Role)

main_bp = Blueprint("main", __name__)


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


################################ View Methods ################################

######## / ########
@main_bp.route("/")
def home_page():
    "Serve home page from index.html."
    return render_template("index.html", sections=SECTIONS)


######## /config ########
@main_bp.route("/config")
@auth_required('session')
def get_version():
    from flask import current_app
    return {
        "server_version": __version__,
        "site_map": site_map(current_app),
        "config": {k: str(v) for (k, v) in current_app.config.items()}
    }


######## /ip ########
@main_bp.route("/ip", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200


######## /note/... [Markdown notes] ########
@main_bp.route("/note/<name>")
def markdown_page(name: str):
    from flask import current_app
    source = current_app.extensions["content"]
    try:
        raw = source.markdown(name)
    except ContentNotFound:
        abort(404)
    except ContentUnavailable:
        abort(502)
    first, _, rest = raw.partition("\n")
    match = re.match(r'^(#+)\s+(.+)', first)
    if match:
        title = match.group(2)
        body = rest
    else:
        title = "Just another holdenweb note"
        body = raw
    return render_template(
        'markdown.html',
        content=md.convert(body),
        title=title,
    )


######## /page/... [HTML page] ########
@main_bp.route("/page/<path:name>/")
def page_from_html(name: str):
    "Serve an HTML page selected by name."
    from flask import current_app
    source = current_app.extensions["content"]
    try:
        raw = source.html(name)
    except ContentNotFound:
        abort(404)
    except ContentUnavailable:
        abort(502)
    page_dir = os.path.dirname(name)
    body = rewrite_asset_urls(raw, page_dir)
    return render_template("base.html", content=body)


######## /asset/... [Proxy for content-app-hosted assets] ########
@main_bp.route("/asset/<path:path>")
def get_asset(path: str):
    from flask import current_app
    source = current_app.extensions["content"]
    try:
        body, ctype = source.asset(path)
    except ContentNotFound:
        abort(404)
    except ContentUnavailable:
        abort(502)
    resp = Response(body, mimetype=ctype)
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


######## /parts/xxxxxxx ########
@main_bp.route("/parts/<number>")
def parts_demo(number: str):
    if number != "demo":
        flash("Sorry, we only do demos at present!")
        abort(404)
    return page_from_html("parts_demo")


######## /python ########
@main_bp.route("/python/<path:path>")
def redirect_to_pbts(path: str):
    return send_from_directory("static/python/web", path)


######## /qrcode/ [form processor] ########
@main_bp.route("/qrcode/", methods=['GET', 'POST'])
def get_or_post_qrcode():
    form = QRcode_Form()
    if form.validate_on_submit():
        text = request.form['qrcode_text']
        qr = qrcode.make(text)
        memfile = io.BytesIO()
        qr.save(memfile)
        memfile.seek(0)
        response = Response(memfile.getvalue(), mimetype="image/gif")
        return response
    return render_template('qrcode_form.html', form=form)


def handle_404(e):
    return render_template("404.html", title="Page not found", content=e), 404


def create_app(config_overrides=None):
    """Application factory.

    `config_overrides` lets callers (tests, alternate entry points) replace
    config values -- e.g. an in-memory database and disabled mail sending --
    without touching the environment.
    """
    app = Flask(__name__, static_url_path='/static/', static_folder='static/')

    # SERVER_NAME enforces strict host matching when set, so only set it if
    # an environment explicitly requests it (e.g. for local dev).
    server_name = os.environ.get("SERVER_NAME")
    if server_name:
        app.config['SERVER_NAME'] = server_name

    app.logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['CONTENT_BASE_URL'] = os.environ.get("CONTENT_BASE_URL")
    app.config['CONTENT_ACCESS_TOKEN'] = os.environ.get("CONTENT_ACCESS_TOKEN")
    app.config['CONTENT_HTTP_TIMEOUT'] = float(
        os.environ.get("CONTENT_HTTP_TIMEOUT", 5.0)
    )
    app.config['CONTENT_CACHE_TTL'] = int(
        os.environ.get("CONTENT_CACHE_TTL", 300)
    )
    app.config['CONTENT_ASSET_CACHE_TTL'] = int(
        os.environ.get("CONTENT_ASSET_CACHE_TTL", 3600)
    )
    app.config['SECURITY_REGISTERABLE'] = True
    app.config["SECURITY_RECOVERABLE"] = True

    app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
    app.config["SESSION_COOKIE_SAMESITE"] = "strict"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    for k in ('MAIL_USERNAME', 'MAIL_DEFAULT_SENDER', 'SECURITY_EMAIL_SENDER'):
        app.config[k] = 'steve@holdenweb.com'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_BACKEND'] = 'smtp'

    if config_overrides:
        app.config.update(config_overrides)

    paranoid.init_app(app)
    paranoid.redirect_view = '/'

    mail.init_app(app)
    db.init_app(app)
    security.init_app(app, user_datastore)

    if app.config.get("CONTENT_BASE_URL"):
        token = app.config.get("CONTENT_ACCESS_TOKEN")
        if not token:
            raise RuntimeError(
                "CONTENT_BASE_URL is set but CONTENT_ACCESS_TOKEN is missing; "
                "refusing to make un-authenticated content fetches."
            )
        app.extensions["content"] = HTTPContentSource(
            base_url=app.config["CONTENT_BASE_URL"],
            token=token,
            timeout=app.config["CONTENT_HTTP_TIMEOUT"],
            text_ttl=app.config["CONTENT_CACHE_TTL"],
            asset_ttl=app.config["CONTENT_ASSET_CACHE_TTL"],
        )
    else:
        app.extensions["content"] = LocalContentSource(Path(str(DATA_PATH)))

    app.register_error_handler(404, handle_404)
    app.register_blueprint(main_bp)
    app.register_blueprint(pdf_blueprint, url_prefix="/pdf/")

    return app


app = create_app()
application = app.wsgi_app

if __name__ == '__main__':
    app.run(port=2400, debug=True)

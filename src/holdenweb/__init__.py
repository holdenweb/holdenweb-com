import os
import io
import qrcode
import re

from dataclasses import dataclass
from importlib.resources import files
from logging import getLogger, basicConfig, DEBUG

import markdown

from dotenv import load_dotenv
from flask import (
    abort,
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)
from flask_mailman import Mail
from flask_paranoid import Paranoid
from flask_security import Security, SQLAlchemyUserDatastore, auth_required
from flask_security.models import fsqla_v3 as fsqla
from flask_sqlalchemy import SQLAlchemy

import holdenweb
from .forms import QRcode_Form
from .pdf import pdf_blueprint
from .version import __version__

load_dotenv()

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

logger = getLogger(__name__)
basicConfig(
    level=DEBUG,
    format='%(filename)s: %(levelname)s: %(message)s',
)

md = markdown.Markdown(extensions=['mdx_math', 'codehilite'])

# The code below should go in a `create-app` function
appfile_dir = "."
app = Flask(__name__, static_url_path='/static/', static_folder='static/')

paranoid = Paranoid(app)
paranoid.redirect_view = '/'

app.config['SERVER_NAME']='localhost'

app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
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

mail = Mail(app)

db = SQLAlchemy(app)
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    pass

class User(db.Model, fsqla.FsUserMixin):
    pass

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

def site_map():
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

@app.errorhandler(404)
def handle_404(e):
    return render_template("404.html", title="Page not found", content=e), 404

################################ View Methods ################################

######## / ########
@app.route("/")
def home_page():
    "Serve home page from index.html."
    return render_template("index.html", sections=SECTIONS)


######## /config ########
@app.route("/config")
@auth_required('session')
def get_version():
    return {
        "server_version": __version__,
        "site_map": site_map(),
        "config": {k: str(v) for (k, v) in app.config.items()}
    }


######## /ip ########
@app.route("/ip", methods=["GET"])
def get_my_ip():
    return jsonify({'ip': request.remote_addr}), 200


######## /note/... [Markdown notes] ########
@app.route("/note/<name>")
def markdown_page(name: str):
    fpath = DATA_PATH / "md-pages" / f"{name}.md"
    if not os.path.commonpath([DATA_PATH, fpath]).startswith(str(DATA_PATH)):
        abort(404)
    title = None
    try:
        with open(fpath) as f:
            title_line = f.readline()
            # Check whether the first line is a title
            match = re.match(r'^(#+)\s+(.+)', title_line)
            if match:
                title = match.group(2)
                content = f.read()
            else:
                title = "Just another holdenweb note"
                content = title_line + f.read()
            html = md.convert(content)
            return render_template(
                'markdown.html',
                content=html,
                title=title
            )
    except OSError:
        abort(404)


######## /page/... [HTML page] ########
@app.route("/page/<path:name>/")
def page_from_html(name: str):
    "Serve an HTML page selected by name."
    fpath = DATA_PATH / "html-pages" / f"{name}.html"
    if not os.path.commonpath([DATA_PATH, fpath]).startswith(str(DATA_PATH)):
        abort(404)
    try:
        with open(fpath) as f:
            return render_template("base.html", content=f.read())
    except OSError:
        abort(404)


######## /parts/xxxxxxx ########
@app.route("/parts/<number>")
def parts_demo(number: str):
    if number != "demo":
        flash("Sorry, we only do demos at present!")
        abort(404)
    return page_from_html("parts_demo")


######## /python-by-the-sea/* ########
@app.route('/python-by-the-sea/', defaults={'v': None})
@app.route('/python-by-the-sea/<path:v>')
def redirect_to_pbts(v: str):
    return redirect("https://python-by-the-sea.org", code=301)


######## /qrcode/ [form processor] ########
@app.route("/qrcode/", methods=['GET', 'POST'])
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

######## /pdf/ [handled by blueprint] ########
app.register_blueprint(pdf_blueprint, url_prefix="/pdf/")

application = app.wsgi_app

if __name__ == '__main__':
    app.run(port=2400, debug=True)

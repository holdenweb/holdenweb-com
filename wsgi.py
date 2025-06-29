import wingdbstub
import os
import io
import itertools
import qrcode
import random
import re
from dataclasses import dataclass
from logging import getLogger, basicConfig, DEBUG
from flask import (
    Flask,
    Response,
    render_template,
    flash,
    request,
    abort,
)
from forms import QRcode_Form
from pdf import pdf_blueprint
import markdown
from version import __version__

appfile_dir = os.path.dirname(__file__)
app = Flask(__name__)

@dataclass
class Section:
    label: str
    path: str

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

request_count = itertools.count()

@app.route("/note/<name>")
def markdown_page(name):
    md = markdown.Markdown(extensions=['mdx_math', 'codehilite'])
    file_path = os.path.join(appfile_dir, "md-pages", f"{name}.md")
    title = None
    try:
        with open(file_path) as f:
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



@app.route("/config")
def get_version():
    return {
        "server_version": __version__
    }


@app.route("/")
def home_page():
    "Serve home page from index.html."
    return render_template("index.html", sections=SECTIONS)


@app.route("/pages/<name>")
def page_from_html(name):
    "Serve an HTML page selected by name."
    try:
        with open(os.path.join(appfile_dir, "html-pages", f"{name}.html")) as f:
            return render_template("base.html", content=f.read())
    except OSError:
        flash(f"Cannot find page {name!r}")
        abort(404)

TEMPLATES = ['p1.html', 'p2.html', 'p3.html', 'p4.html']

@app.route('/python-by-the-sea/', defaults={'v': None})
@app.route('/python-by-the-sea/<v>')
def serve_random_template(v):
    if not v:
        f_name = random.choice(TEMPLATES)
    else:
        f_name = f"p{v}.html"
    # Randomly select one of the templates
    selected_file = f"{appfile_dir}/static/pbs/landing/{f_name}"
    if not os.path.exists(selected_file):
        print(selected_file, "doesn't exist")
        abort(404)
    with open(selected_file) as f:
        return f.read()

@app.route("/parts/<number>")
def parts_demo(number):
    if number != "demo":
        flash("Sorry, we only do demos!")
        abort(404)
    return page_from_html("parts_demo")

@app.route("/qrcode", methods=['GET', 'POST'])
def get_or_post_qrcode():
    form = QRcode_Form()
    logger.info("QR code requested")
    if form.validate_on_submit():
        text = request.form['qrcode_text']
        qr = qrcode.make(text)
        memfile = io.BytesIO()
        qr.save(memfile)
        memfile.seek(0)
        response = Response(memfile.getvalue(), mimetype="image/gif")
        return response
    return render_template('qrcode_form.html', form=form)

app.register_blueprint(pdf_blueprint, url_prefix="/pdf/")

app.config['SECRET_KEY'] = "lkjahskdflkjad[pouaerpoiuqt"
application = app.wsgi_app

if __name__ == '__main__':
    app.run(port=2400, debug=True)

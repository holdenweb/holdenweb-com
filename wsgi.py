import os
import io
import qrcode
from io import BytesIO
from logging import getLogger
from flask import (Blueprint, Flask, Response, render_template, flash,
                   send_file, redirect, request, url_for, abort)
from flask_wtf import FlaskForm
from pdf import pdf_blueprint
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
from zipfile import ZipFile
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown


class QRcode_Form(FlaskForm):
    qrcode_text = StringField('qrcode_text')
    submit = SubmitField('Get QR Code')


appfile_dir = os.path.dirname(__file__)
app = Flask(__name__)


env = Environment(
    loader=FileSystemLoader('%s/templates/' % appfile_dir),
    autoescape=select_autoescape(['html', 'xml'])
)
logger = getLogger(__name__)


@app.route("/page/<name>")
def markdown_page(name):
    md = markdown.Markdown(extensions=['mdx_math'])
    file_path = os.path.join(appfile_dir, "md-pages", f"{name}.md")
    try:
        with open(file_path) as f:
            html = md.convert(f.read())
            return render_template('markdown.html', content=html)
    except OSError as e:
        abort(404)

@app.route("/config")
def get_version():
    return open(os.path.join(appfile_dir, "version.txt")).read()

@app.route("/")
def home_page():
    "Serve static home page from index.html."
    with open(os.path.join(appfile_dir, "index.html")) as f:
        return f.read()

@app.route("/test")
def test_page():
    "Serve test page, if it exists.Z"
    try:
        with open(os.path.join(appfile_dir, "test.html")) as f:
            return f.read()
    except OSError as e:
        abort(404)

@app.route("/notes/<name>")
def page_from_html(name):
    "Serve an HTML page selected by name."
    with open(os.path.join(appfile_dir, "html-pages", f"{name}.html")) as f:
        return render_template("base.html", content=f.read())

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
    app.run(port=2400)

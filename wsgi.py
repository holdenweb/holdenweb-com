import os
import io
import itertools
import time
import qrcode
from dataclasses import dataclass
from io import BytesIO
from logging import getLogger, basicConfig, DEBUG
from flask import (Blueprint, Flask, Response, render_template, flash,
                   send_file, redirect, request, url_for, abort)
from flask_wtf import FlaskForm
from pdf import pdf_blueprint
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
from zipfile import ZipFile
import markdown
from version import __version__
import dotenv

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
    format='%(filename)s: %(levelname)s: %(funcName)s:%(lineno)d:%(message)s'
)

request_count = itertools.count()

#@app.before_request
#def request_start():
    #request.start_time = time.time()
    #request.id = next(request_count)
    #logger.debug(f"Request {request.id}h: {request.url}")


#@app.after_request
#def request_end(resp):
    #logger.debug(f"Request {request.id} ended, duration {time.time() - request.start_time:5.2f}")
    #return resp



class QRcode_Form(FlaskForm):
    qrcode_text = StringField('qrcode_text')
    submit = SubmitField('Get QR Code')


@app.route("/note/<name>")
def markdown_page(name):
    md = markdown.Markdown(extensions=['mdx_math', 'codehilite'])
    file_path = os.path.join(appfile_dir, "md-pages", f"{name}.md")
    try:
        with open(file_path) as f:
            html = md.convert(f.read())
            return render_template('markdown.html', content=html)
    except OSError as e:
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
    except OSError as e:
        flash(f"No page called {name!r}")
        abort(404)

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
    app.run(port=2400)

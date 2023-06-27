import os
import io
import sys
from io import BytesIO
from booklet import make_booklet
from flask import (Blueprint, Flask, Response, render_template, flash,
                   send_file, redirect, request, url_for)
from flask_wtf import FlaskForm
import qrcode
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import DataRequired
from zipfile import ZipFile
from logging import getLogger
import pdfrw
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown


class PDF_Form(FlaskForm):
    file_details = FileField('file_details', validators=[DataRequired()])
    file_prefix = StringField('file_prefix')
    submit = SubmitField('Get Pages')

class QRcode_Form(FlaskForm):
    qrcode_text = StringField('qrcode_text')
    submit = SubmitField('Get QR Code')

class BookletForm(FlaskForm):
    file_details = FileField('file_details', validators=[DataRequired()])
    submit = SubmitField("Generate Booklet")


appfile_dir = os.path.dirname(__file__)
app = Flask(__name__)


env = Environment(
    loader=FileSystemLoader('%s/templates/' % appfile_dir),
    autoescape=select_autoescape(['html', 'xml'])
)
logger = getLogger(__name__)


@app.route("/page/<name>")
def parent_page(name):
    md = markdown.Markdown(extensions=['mdx_math'])
    with open(os.path.join(appfile_dir, "md-pages", f"{name}.md")) as f:
        html = md.convert(f.read())
        return render_template('markdown.html', content=html)

@app.route("/version")
def get_version():
    return open(os.path.join(appfile_dir, "version.txt")).read()

@app.route("/")
def home_page():
    with open(os.path.join(appfile_dir, "index.html")) as f:
        return f.read()

@app.route("/notes/<name>")
def page_from_html(name):
    with open(os.path.join(appfile_dir, "html-pages", f"{name}.html")) as f:
        return render_template("base.html", content=f.read())

@app.route("/pdf/pagezip", methods=['GET', 'POST'])
def get_or_post_pagezip():
    form = PDF_Form()
    logger.info(f"Page split requested")
    if form.validate_on_submit():
        my_file = request.files['file_details']
        file_prefix = request.form['file_prefix'] or 'page'
        try:
            inputpdf = pdfrw.PdfReader(fname=my_file.stream)
            outfiles = []
            outzip = BytesIO()
            container = ZipFile(outzip, 'w')
            for i, page in enumerate(inputpdf.pages):
                output = pdfrw.PdfWriter()
                file_name = f"{file_prefix}_{i+1:03}.pdf"
                output.addpage(page)
                outfile = BytesIO()
                output.write(outfile)
                container.writestr(f"pdf/{file_name}",
                                   outfile.getvalue())
            container.close()
            outzip.seek(0)
            return send_file(outzip,
                             mimetype="application/octet-stream",
                             as_attachment=True,
                             download_name="pages.zip")
        except Exception:
            flash(f"Could not open file as a PDF - please try again")
            raise
    return render_template('pagesplit_form.html', form=form)


@app.route("/pdf/booklet", methods=['GET', 'POST'])
def get_or_post_booklet():
    form = BookletForm()
    logger.info("Booklet requested")
    if form.validate_on_submit():
        my_file = request.files['file_details']
        try:
            output_pdfs = make_booklet(my_file.stream)
            outzip = BytesIO()
            container = ZipFile(outzip, 'w')
            for p_typ, pdf in zip(('odd', 'even'), output_pdfs):
                container.writestr(f"pdf/{p_typ}.pdf",
                                   pdf.getvalue())
            container.close()
            outzip.seek(0)
            return send_file(outzip,
                             mimetype="application/zip",
                             as_attachment=True,
                             download_name="pages.zip")
        except Exception as e:
            return f"I'm sorry, Dave, it seems I couldn't do that:\n{e}"
    return render_template('booklet_form.html', form=form)

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

app.config['SECRET_KEY'] = "lkjahskdflkjad[pouaerpoiuqt"
application = app.wsgi_app

if __name__ == '__main__':

    app.run(port=2400)

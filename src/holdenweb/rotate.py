"""
booklet.py: Produce an 8-page booklet from a single sheet of
paper printed duplex.
"""
import io
import sys
from itertools import cycle
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


def make_booklet(in_doc: str, out_doc: ):
    pages = PdfReader(in_doc).pages
    canvas = Canvas(out_doc)
    canvas.setPageSize(A4)
    for page in pages:
        page = makerl(canvas, pagexobj(page))
        canvas.rotate(180)
        canvas.doForm(page)
        canvas.showPage()
    canvas.save()

if __name__ == '__main__':
    make_booklet(sys.argv[1], open("test.pdf", 'wb'))


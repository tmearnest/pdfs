import hashlib
import os

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBox
from pdfminer.converter import PDFPageAggregator
from .Cache import cachedRequest

from unidecode import unidecode
from .Logging import log

def getPdfTxt(fname):
    return _getPdfTxt(fname, cache_key=md5sum(fname))

@cachedRequest("PDF")
def _getPdfTxt(fname, cache_key=None):
    with open(fname, "rb") as fp: 
        log.info("Parsing pdf file: " + os.path.basename(fname))
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = PDFDevice(rsrcmgr)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = []

        def extractText(g):
            if isinstance(g, LTTextBox):
                return [g.get_text()]
            try:
                return sum((extractText(x) for x in g), [])
            except TypeError:
                return []

        pages = []

        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            pages.append(unidecode(' '.join(sum((x.split() for x in extractText(layout)), []))))

        return pages

def md5sum(fname):
    return hashlib.md5(open(fname,"rb").read()).hexdigest()

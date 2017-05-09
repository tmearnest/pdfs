from pybtex.database import parse_string, BibliographyData
from pybtex.backends.html import Backend
from pybtex.style.formatting.unsrt import Style as Unsrt

import flask
import os, io
from . import *
from . Db import DB


class HtmlBackend(Backend):
    def write_entry(self, key, label, text):
        self.output('<dt><a href="/{key}.pdf" target="_blank">{key}</a></dt>\n'.format(key=key))
        self.output('<dd>{text}</dd>\n'.format(text=text))

def launchWWW(args):
    dirs = args.dirs

    flaskApp = flask.Flask("sbd", template_folder=os.path.join(os.path.dirname(__file__),"templates"))

    @flaskApp.route('/<key>.pdf')
    def getPdf(key):
        resp = flask.make_response(open(os.path.join(args.dirs.pdf,key+".pdf"), "rb").read())
        resp.content_type = 'application/pdf'
        return resp

    @flaskApp.route('/')
    def listFiles():
        db = DB(dirs.db)
        style = Unsrt()
        bdb = db.getAll()
        keys = list(bdb.entries.keys())
        formatted_bibliography = style.format_bibliography(bdb, keys)
        f = io.StringIO()
        be = HtmlBackend(None)
        be.write_to_stream(formatted_bibliography, f)
        resp = flask.make_response(f.getvalue())
        resp.content_type = 'text/html'
        return resp

    flaskApp.run()

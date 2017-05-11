import flask
import os
from . Db import DB
from . BibFormat import formatBibEntriesHTML

def cmd_www(args):
    flaskApp = flask.Flask("sbd", template_folder=os.path.join(os.path.dirname(__file__),"templates"))

    @flaskApp.route('/<key>.pdf')
    def getPdf(key):
        resp = flask.make_response(open(os.path.join(args.pdfDir,key+".pdf"), "rb").read())
        resp.content_type = 'application/pdf'
        return resp

    @flaskApp.route('/')
    def listFiles():
        db = DB(args.dbFile)
        bdb = db.getAll()
        keys = list(bdb.entries.keys())
        resp = flask.make_response(formatBibEntriesHTML(bdb, keys))
        resp.content_type = 'text/html'
        return resp

    flaskApp.run()

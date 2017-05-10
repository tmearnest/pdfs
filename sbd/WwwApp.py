import flask
import os
from . Db import DB
from . BibFormat import formatBibEntriesHTML

def cmd_www(args):
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
        bdb = db.getAll()
        keys = list(bdb.entries.keys())
        resp = flask.make_response(formatBibEntriesHTML(bdb, keys))
        resp.content_type = 'text/html'
        return resp

    flaskApp.run()

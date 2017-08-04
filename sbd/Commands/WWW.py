import flask
import mimetypes
import os
import json

from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters import HtmlFormatter

from .Command import Command
from ..Database import Database
from ..HTMLBib import htmlBibliography
from .. import UserException

_htmlBoilerplate = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>{title}</title>
  </head>
  <body>
  {body}
  </body>
</html>
"""

class WWW(Command):
    command = 'www'
    help = "Spin up http server"

    def set_args(self, subparser):
        subparser.add_argument("--port","-P", help="Port number to listen on", type=int, default=5000)

    def run(self, args):
        Database(dataDir=args.data_dir)
        flaskApp = flask.Flask("sbd")

        @flaskApp.route('/<key>.pdf')
        def getPdf(key):
            db = Database(dataDir=args.data_dir)
            try:
                pdfFile = next(filter(lambda x: x.key() == key, db.works)).files[0]
            except StopIteration:
                raise KeyError
            resp = flask.make_response(open(os.path.join(db.dataDir, pdfFile), "rb").read())
            resp.content_type = 'application/pdf'
            return resp

        @flaskApp.route('/attachment/<string:key>-<int:idx>.<string:ext>')
        def getAttached(key, idx, ext):
            db = Database(dataDir=args.data_dir)
            try:
                attFile = next(filter(lambda x: x.key() == key, db.works)).files[idx]
            except StopIteration:
                raise KeyError

            filePath = os.path.join(db.dataDir, attFile)
            resp = flask.make_response(open(filePath, "rb").read())
            mime, _ = mimetypes.guess_type(filePath)
            resp.content_type = mime or 'application/octet-stream'
            return resp



        @flaskApp.route('/<key>.bib')
        def getBib(key):
            db = Database(dataDir=args.data_dir)
            try:
                e = next(filter(lambda x: x.key() == key, db.works))
            except StopIteration:
                raise KeyError
            resp = flask.make_response(e.bibtex)
            resp.content_type = 'text/plain'
            return resp


        @flaskApp.route("/metadata/<key>")
        def getMeta(key):
            db = Database(dataDir=args.data_dir)
            try:
                e = next(filter(lambda x: x.key() == key, db.works))
            except StopIteration:
                raise KeyError
            html = highlight(json.dumps(e.meta, indent=4, sort_keys=True),JsonLexer(), HtmlFormatter(noclasses=True))

            resp = flask.make_response(_htmlBoilerplate.format(title="sdb: {} metadata".format(key), body=html))
            resp.content_type = 'text/html'
            return resp

        @flaskApp.route('/')
        def listFiles():
            db = Database(dataDir=args.data_dir)
            bib = htmlBibliography(sorted(db.works, key=lambda x: x.key()), directory=os.path.basename(os.path.dirname(db.dataDir)))
            resp = flask.make_response(bib)
            resp.content_type = 'text/html'
            return resp

        try:
            flaskApp.run(port=args.port)
        except OSError as err:
            if 'Address already in use' in str(err):
                raise UserException("Port {} already in use.".format(args.port))

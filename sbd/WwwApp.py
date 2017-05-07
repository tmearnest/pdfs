import flask
import os
from . import *
from . Search import Search

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
        s = Search(dirs.index)
        return flask.render_template("index.html", results=s.listAll())

    flaskApp.run()

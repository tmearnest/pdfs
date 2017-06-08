import flask
import os
from markdown import markdown
from pybtex.database import BibliographyData
import pypandoc

from . Db import DB
from . BibFormat import formatBibEntriesHTML
from . TextSearch import TextSearch

def _tohtml(s):
    return pypandoc.convert_text(s, 'plain', format='latex').strip()

def cmd_www(args):
    s = TextSearch(args.indexDir)
    db = DB(args.dbFile)
    templateDir = os.path.join(os.path.dirname(__file__),"templates")
    flaskApp = flask.Flask("sbd", template_folder=templateDir)

    def entryContext(citeKey):
        bdb = db.lookup('citeKey', citeKey)
        e = bdb.entries[citeKey]
        ctx = dict()
        
        authors = e.persons['author'] or e.persons['editor']
        if len(authors) == 1:
            ctx['authors'] = ' '.join(authors[0].last_names)
        elif len(authors) == 2:
             ctx['authors'] = ' and '.join(' '.join(a.last_names) for  a in authors)
        elif len(authors) == 3:
            a1 = ' '.join(authors[0].last_names)
            a2 = ' '.join(authors[1].last_names)
            a3 = ' '.join(authors[2].last_names)
            ctx['authors'] = '{}, {}, and {}'.format(a1,a2,a3)
        else: 
            ctx['authors'] = ' '.join(authors[0].last_names) + " et al."

        ctx['title'] = e.fields.get("title") or e.fields.get("booktitle") or e.fields.get("series") or ""
        ctx['year'] = e.fields['year']
        ctx['doi'] = e.fields['doi']
        ctx['journal'] = (e.fields.get("journal") or e.fields.get("institution") 
                           or e.fields.get("organization") or e.fields.get("school") or "")

        ctx = {x: _tohtml(y) for x,y in ctx.items()}

        ctx['abstract'] = e.fields.get("annote") or ""
        ctx['citation'] = formatBibEntriesHTML(bdb, [citeKey], fragment=True)
        note = s.getNote(citeKey)
        if note:
            ctx['note'] = markdown(note)
        ctx['tags'] = db.getTags(citeKey)
        ctx['key'] = citeKey

        return ctx



    @flaskApp.route("/style.css")
    def style():
        resp = flask.make_response(open(os.path.join(templateDir,"style.css"), "r").read())
        resp.content_type = 'text/css'
        return resp

    @flaskApp.route('/entry/<citeKey>')
    def getArticleContext(citeKey):
        return flask.render_template('single.html', **entryContext(citeKey))

    @flaskApp.route("/search")
    def search():
        return flask.render_template('search.html', results=[entryContext(k) for k in db.getAllKeys()])


    @flaskApp.route('/pdf/<key>.pdf')
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

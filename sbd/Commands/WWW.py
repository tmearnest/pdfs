from .Command import Command

def mkTagList(db):
    if db.tags:
        return ' '.join('<a class="tags" href="/tag/{0}">{0}</a>'.format(t) for t in sorted(db.tags))

class WWW(Command):
    command = 'www'
    help = "Spin up http server"

    def set_args(self, subparser):
        subparser.add_argument("--port","-P", help="Port number to listen on", type=int, default=5000)

    def run(self, args):
        import logging
        import mimetypes
        import os

        import flask
        import jinja2

        from ..Database import Database
        from ..HTMLBib import bibContext, authorNorm
        from ..Exceptions import UserException
                
        if not args.debug:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

        Database(dataDir=args.data_dir)
        flaskApp = flask.Flask("sbd")
        flaskApp.jinja_env.trim_blocks = True
        flaskApp.jinja_env.lstrip_blocks = True
        flaskApp.jinja_loader=jinja2.PackageLoader("sbd")

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

        @flaskApp.route('/tag/<tag>')
        def listFilesByTag(tag):
            db = Database(dataDir=args.data_dir)
            matches = sorted(filter(lambda x: tag in x.tags, db.works), key=lambda x: x.key())

            ctx = dict(entries=bibContext(matches),
                       article_dir=os.path.basename(os.path.dirname(db.dataDir)), 
                       search="tag:"+tag,
                       tags=mkTagList(db))
            return flask.render_template('bibliography.html', **ctx)

        @flaskApp.route('/')
        def listFiles():
            db = Database(dataDir=args.data_dir)
            ctx = dict(entries=bibContext(sorted(db.works, key=lambda x: x.key())),
                       article_dir=os.path.basename(os.path.dirname(db.dataDir)), 
                       tags=mkTagList(db))
            return flask.render_template('bibliography.html', **ctx)

        @flaskApp.route('/author/<author>')
        def listFilesByAuthor(author):
            db = Database(dataDir=args.data_dir)

            def isAuth(e):
                n, au, ed = set(), e.author(), e.editor()
                if au:
                    n.update(authorNorm(x.split(', ')[0]) for x in au.split(' and '))
                if ed:
                    n.update(authorNorm(x.split(', ')[0]) for x in ed.split(' and '))
                return author in n

            matches = sorted(filter(isAuth, db.works), key=lambda x: x.key())

            ctx = dict(entries=bibContext(matches),
                       article_dir=os.path.basename(os.path.dirname(db.dataDir)), 
                       search="au:"+author,
                       tags=mkTagList(db))
            return flask.render_template('bibliography.html', **ctx)


        @flaskApp.route('/new')
        def listFilesNew():
            db = Database(dataDir=args.data_dir)
            def key(x):
                d = x.importDate
                return (-d.year, 
                        -d.month, 
                        -d.day, 
                        -d.hour, 
                        -d.minute, 
                        -d.second, 
                        x.key())
            ctx = dict(entries=bibContext(sorted(db.works, key=key)),
                       article_dir=os.path.basename(os.path.dirname(db.dataDir)), 
                       tags=mkTagList(db))
            return flask.render_template('bibliography.html', **ctx)

        try:
            flaskApp.run(port=args.port)
        except OSError as err:
            if 'Address already in use' in str(err):
                raise UserException("Port {} already in use.".format(args.port))

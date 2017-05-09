import inotify.adapters
import os, argparse, shutil
import termcolor as tc
import tempfile
from . import *
from .Pdf import *
from .Doi import *
from .Search import *
from .Db import DB
from .Metadata import DoiLookup
from pybtex.database import parse_file

def _stripAnsi(s):
    return re.sub(r'\x1b[^m]*m', ' ', s)

class EntryExistsError(Exception):
    pass

class DoiFailureError(Exception):
    pass


def dbInit(args):
    dirs = args.dirs

    for x in [dirs.root, dirs.index, dirs.pdf]:
        try:
            os.mkdir(x)
        except FileExistsError:
            pass

    Search.initialize(dirs.index)
    DB.initialize(dirs.db)
    print("initialized new database at: "+dirs.root)


def dbWatch(args):
    wd = os.path.abspath(args.watchDir)
    inot = inotify.adapters.Inotify()
    inot.add_watch(wd.encode())
    pinfo("Watching {} for new pdf files...".format(wd))
    try:
        for event in inot.event_gen():
            if event is not None:
                header, type_names, watch_path, filename = event
                if 'IN_CREATE' in type_names:
                    newFile = filename.decode("utf-8")
                    if newFile.lower().endswith(".pdf") and newFile[0] != '.':
                        pinfo("new file: " + newFile)
                        args.file = os.path.join(wd, newFile)
                        args.doi = None
                        try:
                            _dbAdd(args)
                        except (EntryExistsError, AbortException):
                            pass
    except KeyboardInterrupt:
        pass
    finally:
        inot.remove_watch(wd)


def dbAdd(args):
    try:
        _dbAdd(args)
    except EntryExistsError:
        sys.exit(1)
    except AbortException:
        sys.exit(1)

def _dbAdd(args):
    fname = args.file
    dirs = args.dirs
    s = Search(dirs.index)
    db = DB(dirs.db)
    doiLookup = DoiLookup(dirs.doicache)
    getPdfTxt = GetPdfTxt(dirs.pdfcache)

    md5 = md5sum(fname)
    bibs = db.lookup("pdfMd5", md5)

    if bibs is not None:
        key = bibs.entries.keys()[0]
        perror("File already in db under key {}".format(key))
        raise EntryExistsError
    txt = getPdfTxt(fname)

    if args.doi is not None:
        doi = args.doi
        bibObj = doiLookup(doi)
    else:
        bibObj = selectDoi(' '.join(txt), fname, doiLookup)
        if bibObj is None:
            bibObj = doiEntry(fname, doiLookup)

    if bibObj is None:
        perror("Doi lookup failed")
        raise DoiFailureError

    
    key = bibObj.entries.keys()[0]
    bibs = db.lookup("citeKey", key)
    if bibs is not None:
        perror("Doi already in db under key {}".format(key))
        raise EntryExistsError

    baseKey,suffix = key, '`'
    while db.lookup("citeKey", key) is not None:
        suffix = chr(ord(suffix)+1)
        key = baseKey + suffix
    if key != baseKey:
        bibObj = rekey(bibObj, key)

    s.addFulltext(key, txt)
    shutil.copy(fname, os.path.join(dirs.pdf, key+".pdf"))

    db.addBibtex(bibObj, md5)
    print("Imported " + tc.colored(os.path.basename(fname), "green") + " as")
    print(formatBibEntries(bibObj, [key], show_numbers=False))



def dbSearch(args):
    dirs = args.dirs
    s = Search(dirs.index)
    db = DB(dirs.db)

    terms = ' '.join(args.terms)

    if args.text:
        firstLine = True

        for key, pages in s.search(terms):
            bib = db.lookup('citeKey', key)
            if not args.no_context:
                if firstLine:
                    firstLine = False
                else:
                    print()
                    print("="*80)
                    print()

            print(formatBibEntries(bib, [key], show_numbers=False))
            if not args.no_context:
                print()

                for r in pages:
                    page = r['page']
                    context = r['text']
                    score = r['score']
                    print("page " + tc.colored(str(page+1), "yellow") + ", score " + tc.colored(" {:.3f}".format(score), "blue"))
                    print(context)
                    print()

                pth = "file://" + os.path.abspath(os.path.join(dirs.pdf, key + ".pdf"))
                print(tc.colored(pth, "green"))
        return

    if args.tag:
        rs = db.lookup("tag", terms)
    elif args.author:
        rs = db.lookup("authors", terms)
    elif args.editor:
        rs = db.lookup("editors", terms)
    elif args.title:
        rs = db.lookup("title", terms)
    elif args.journal:
        rs = db.lookup("journal", terms)
    elif args.year:
        rs = db.lookup("year", terms)
    elif args.cite_key:
        rs = db.lookup("citeKey", terms)
    elif args.doi:
        rs = db.lookup("doi", terms)
    else:
        raise NotImplementedError

    print(formatBibEntries(rs, rs.entries.keys(), show_numbers=False))



def dbBib(args):
    dirs = args.dirs
    s = Search(dirs.index)
    db = DB(dirs.db)
    if args.all:
        bd = db.getAll()
    else:
        raise NotImplementedError

    print(bd.to_string("bibtex"))

def dbEdit(args):
    dirs = args.dirs
    s = Search(dirs.index)
    db = DB(dirs.db)
    oldKey = args.key
    oldCollection = db.lookup("citeKey", oldKey)
    bibtex = oldCollection.to_string("bibtex")
    tmpf,tmpfname = tempfile.mkstemp(suffix=".bib", text=True)
    os.write(tmpf, bibtex.encode())
    os.close(tmpf)
    editor=os.environ.get("VISUAL") or "vi"
    os.system("{} {}".format(editor, tmpfname))
    newBibtex = open(tmpfname).read()
    if newBibtex == bibtex:
        perror("not modified")
        sys.exit(0)
    collection = parse_file(tmpfname)
    newKey = collection.entries.keys()[0]
    db.modBibtex(oldKey, collection)
    shutil.move(os.path.join(dirs.pdf, oldKey+".pdf"), os.path.join(dirs.pdf, newKey+".pdf"))


def dbModTags(args):
    dirs = args.dirs
    db = DB(dirs.db)
    key = args.key
    tags = ["+" + t for t in args.add] + ["-" + t for t in args.remove]
    if len(tags) == 0:
        print(db.getTags(key))
    else:
        db.modTags(key, tags)

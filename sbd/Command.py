import inotify.adapters
import os, argparse, shutil
import termcolor as tc
from .Pdf import *
from .Doi import *
from .Search import *

def _stripAnsi(s):
    return re.sub(r'\x1b[^m]*m', ' ', s)

class PdfExistsError(Exception):
    pass


def dbInit(args):
    dirs = args.dirs

    for x in [dirs.root, dirs.index, dirs.pdf]:
        try:
            os.mkdir(x)
        except FileExistsError:
            pass

    Search.initialize(dirs.index)
    print("initialized new database at: "+dirs.root)



def dbWatch(args):
    wd = args.watchDir.encode()
    inot = inotify.adapters.Inotify()

    inot.add_watch(wd)
    try:
        for event in inot.event_gen():
            if event is not None:
                header, type_names, watch_path, filename = event
                if 'IN_CREATE' in type_names:
                    newFile = filename.decode("utf-8")
                    print("new file: ", newFile)
                    args.file = newFile
                    args.doi = None
                    try:
                        _dbAdd(args)
                    except (PdfExistsError, AbortException):
                        pass
    except KeyboardInterrupt:
        pass
    finally:
        inot.remove_watch(wd)


def dbAdd(args):
    try:
        _dbAdd(args)
    except PdfExistsError:
        sys.exit(1)
    except AbortException:
        sys.exit(1)

def _dbAdd(args):
    fname = args.file
    dirs = args.dirs
    s = Search(dirs.index)

    md5 = md5sum(fname)

    key = s.findByMd5(md5)
    if key:
        perror("File already in db under key {}".format(key))
        raise PdfExistsError
    txt = getPdfTxt(fname)

    if args.doi is not None:
        doi = args.doi
        bibObj = doi2bibtex(doi)
    else:
        bibObj = selectDoi(' '.join(txt), fname)
        if bibObj is None:
            bibObj = doiEntry(fname)

    key = bibObj['key']
    baseKey,suffix = key, '`'
    while s.keyExists(key):
        suffix = chr(ord(suffix)+1)
        key = baseKey + suffix
    if key != baseKey:
        bibObj = rekey(bibObj, key)
    bib = bibObj['bibCollection'].to_string("bibtex")

    s.addFulltext(dict(key=key, 
                       md5=md5, 
                       doi=bibObj['doi'],
                       bib=bib,
                       authors=bibObj['authors'],
                       title=bibObj['title'],
                       year=bibObj['year'],
                       pub=bibObj['pub']), 
                  txt)
    shutil.copy(fname, os.path.join(dirs.pdf, key+".pdf"))

    print("Imported " + tc.colored(os.path.basename(fname), "green") + " as")
    print(formatBibEntries(bibObj['bibCollection'], [key], show_numbers=False))


def dbSearch(args):
    dirs = args.dirs
    s = Search(dirs.index)

    if args.text:
        firstLine = True

        for r in s.search(' '.join(args.terms)):
            bib = parse_string(r['bibtex'], "bibtex")
            keys = [bib.entries[bib.entries.keys()[0]].key]
            if firstLine:
                firstLine = False
            else:
                print()
                print("="*80)
                print()

            print(formatBibEntries(bib, keys, show_numbers=False))
            print()

            for score,page,context in zip(r['pageScores'], r['pages'], r['text']):
                print("page " + tc.colored(str(page+1), "yellow") + ", score " + tc.colored(" {:.3f}".format(score), "blue"))
                print(context)
                print()

            pth = "file://" + os.path.abspath(os.path.join(dirs.pdf, keys[0] + ".pdf"))
            print(tc.colored(pth, "green"))
    else:
        if args.title:
            key = 'title'
        elif args.year:
            key = 'year'
        elif args.doi:
            key = "doi"
        elif args.journal:
            key = "pub"
        elif args.author:
            key = "authors"
        elif args.cite_key:
            key = "key"
        else:
            raise RuntimeError

        keys = ['key', 'bibtex', 'authors', 'title', 'year', 'pub', 'doi']
        w = max(len(k) for k in keys) + 2
        for r in s.searchKey(key, ' '.join(args.terms)):
            pth = "file://" + os.path.abspath(os.path.join(dirs.pdf, _stripAnsi(r['key']) + ".pdf"))
            print(tc.colored(pth, "green"))
            for k in ['key', 'authors', 'title', 'year', 'pub', 'doi']:
                print(tc.colored("{s:<{w}s}".format(s=k,w=w), "blue"),  end='')
                print(textwrap.fill(str(r[k]).strip(), width=80, initial_indent="", subsequent_indent=" "*w ))
            print()


def dbBib(args):
    dirs = args.dirs
    s = Search(dirs.index)
    if args.all:
        bd = s.getBibTex()
    else:
        bd = sum((s.getBibTex(k) for k in args.key), [])

    for b in bd:
        print(b)


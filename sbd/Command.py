import os, argparse, shutil
import termcolor as tc
from .Pdf import *
from .Doi import *
from .Search import *

def dbInit(args):
    dirs = args.dirs

    for x in [dirs.root, dirs.index, dirs.pdf]:
        try:
            os.mkdir(x)
        except FileExistsError:
            pass

    Search.initialize(dirs.index)
    print("initialized new database at: "+dirs.root)

def dbAdd(args):
    fname = args.file
    dirs = args.dirs
    s = Search(dirs.index)

    md5 = md5sum(fname)

    key = s.findByMd5(md5)
    if key:
        print("File already in db under key {}".format(key))
        sys.exit(1)
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




def dbBib(args):
    dirs = args.dirs
    s = Search(dirs.index)
    if args.all:
        bd = s.getBibTex()
    else:
        bd = sum((s.getBibTex(k) for k in args.key), [])

    for b in bd:
        print(b)


import os
import shutil
import shlex
import sys
import tempfile
import inotify.adapters
import termcolor as tc
from pybtex.database import parse_string

from . Logging import log
from .CaptureDoi import AbortException, doiEntry, selectDoi
from .Pdf import getPdfTxt, md5sum
from .Metadata import doiLookup, pmidAbstractLookup
from .Db import DB
from .TextSearch import TextSearch
from .BibFormat import formatBibEntries, concatBibliography, rekey, bibSingleEntry

class EntryExistsError(Exception):
    pass

class DoiFailureError(Exception):
    pass

def cmd_init(args):
    if args.force:
        try:
            shutil.rmtree(args.indexDir)
            shutil.rmtree(args.pdfDir)
            os.unlink(args.dbFile)
        except:
            pass

    for x in [args.sbdbDir, args.indexDir, args.pdfDir]:
        try:
            os.mkdir(x)
        except FileExistsError:
            pass

    if os.listdir(args.indexDir):
        log.error("Cowardly refusing to clobber an existing index.")
        sys.exit(1)
    TextSearch.initialize(args.indexDir)

    if os.path.exists(args.dbFile):
        log.error("Cowardly refusing to clobber an existing database.")
        sys.exit(1)

    DB.initialize(args.dbFile)
    log.info("Initialized new database at: %s", args.sbdbDir)


def cmd_watch(args):
    wd = os.path.abspath(args.watchDir)
    inot = inotify.adapters.Inotify()
    inot.add_watch(wd.encode())
    log.info("Watching %s for new pdf files...", wd)
    try:
        for event in inot.event_gen():
            if event is not None:
                header, type_names, watch_path, filename = event
                if 'IN_CREATE' in type_names:
                    newFile = filename.decode("utf-8")
                    if newFile.lower().endswith(".pdf") and newFile[0] != '.':
                        log.info("new file: %s",  newFile)
                        args.file = os.path.join(wd, newFile)
                        args.doi = None
                        try:
                            _addFile(args)
                        except (EntryExistsError, AbortException):
                            pass
    except KeyboardInterrupt:
        pass
    finally:
        inot.remove_watch(wd)


def cmd_add(args):
    try:
        _addFile(args)
    except EntryExistsError:
        sys.exit(1)
    except AbortException:
        sys.exit(1)


def _addFile(args):
    fname = args.file
    s = TextSearch(args.indexDir)
    db = DB(args.dbFile)

    md5 = md5sum(fname)
    bibs = db.lookup("pdfMd5", md5)

    if bibs is not None:
        key = bibs.entries.keys()[0]
        log.error("File already in db under key %s", key)
        raise EntryExistsError
    txt = getPdfTxt(fname)

    if args.doi is not None:
        doi = args.doi
        bibObj = doiLookup(doi)
    else:
        bibObj = selectDoi(' '.join(txt), fname, doiLookup)
        if bibObj is None:
            bibObj = doiEntry(fname, doiLookup)
        doi = bibSingleEntry(bibObj).fields['doi']


    if bibObj is None:
        log.error("Doi lookup failed")
        raise DoiFailureError

    pmid, abstract = pmidAbstractLookup(doi)
    
    key = bibObj.entries.keys()[0]
    bibs = db.lookup("citeKey", key)
    if bibs is not None:
        log.error("Doi already in db under key %s", key)
        raise EntryExistsError

    baseKey,suffix = key, '`'
    while db.lookup("citeKey", key) is not None:
        suffix = chr(ord(suffix)+1)
        key = baseKey + suffix
    if key != baseKey:
        bibObj = rekey(bibObj, key)

    s.addFulltext(key, txt)
    shutil.copy(fname, os.path.join(args.pdfDir, key+".pdf"))

    db.addBibtex(bibObj, md5, abstract, pmid)
    print("Imported " + tc.colored(os.path.basename(fname), "green") + " as")
    print(formatBibEntries(bibObj, [key], show_numbers=False))
    print()


def cmd_search(args):
    s = TextSearch(args.indexDir)
    db = DB(args.dbFile)

    terms = ' '.join(args.terms)

    if args.text:
        firstLine = True
        resultCt = 0

        for key, pages in s.search(terms):
            resultCt += 1
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
        log.info("%s result%s", "No" if resultCt == 0 else str(resultCt), "" if resultCt == 1 else "s")
        return
    elif args.note:
        firstLine = True

        resultCt = 0

        for key, r in s.searchNote(terms):
            resultCt += 1
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
                context = r['text']
                score = r['score']
                print("score " + tc.colored(" {:.3f}".format(score), "blue"))
                print(context)
                print()
        log.info("%s result%s", "No" if resultCt == 0 else str(resultCt), "" if resultCt == 1 else "s")
        return
    elif args.tag:
        rs = db.lookup("tag", terms)
    elif args.author:
        rs = db.lookup("authors", terms)
    elif args.editor:
        rs = db.lookup("editors", terms)
    elif args.title:
        rs = db.lookup("bk_title", terms)
    elif args.journal:
        rs = db.lookup("bk_journal", terms)
    elif args.year:
        rs = db.lookup("bk_year", terms)
    elif args.cite_key:
        rs = db.lookup("citeKey", terms)
    elif args.pmid:
        rs = db.lookup("pmid", terms)
    elif args.abstract:
        rs = db.lookup("bk_annote", terms)
    elif args.doi:
        rs = db.lookup("bk_doi", terms)
    else:
        raise NotImplementedError

    if rs is not None:
        print(formatBibEntries(rs, rs.entries.keys(), show_numbers=False))

    resultCt = 0 if not rs else len(rs.entries)

    log.info("%s result%s", "No" if resultCt == 0 else str(resultCt), "" if resultCt == 1 else "s")


def cmd_export(args):
    db = DB(args.dbFile)

    for key, bib in db.getAll().entries.items():
        fname = os.path.realpath(os.path.join(args.pdfDir,key+".pdf"))
        print("sbd add {} --doi {}".format(shlex.quote(fname), shlex.quote(bib.fields['doi'])))

def cmd_bibtex(args):
    db = DB(args.dbFile)
    if args.all:
        bd = db.getAll()
    else:
        bd = concatBibliography([db.lookup('citeKey', k) for k in args.keys])

    print(bd.to_string("bibtex"))


def spawnEditor(text, filetype='txt'):
    tmpf,tmpfname = tempfile.mkstemp(suffix="."+filetype, text=True)
    os.write(tmpf, text.encode())
    os.close(tmpf)
    editor=os.environ.get("VISUAL") or "vi"
    os.system("{} {}".format(editor, tmpfname))
    newText = open(tmpfname).read()
    os.unlink(tmpfname)
    return newText

def cmd_edit(args):
    db = DB(args.dbFile)
    s = TextSearch(args.indexDir)
    oldKey = args.key
    oldCollection = db.lookup("citeKey", oldKey)
    bibtex = oldCollection.to_string("bibtex")
    newBibtex = spawnEditor(bibtex, "bib")
    if newBibtex == bibtex:
        log.warning("not modified")
        sys.exit(0)
    collection = parse_string(newBibtex, "bibtex")
    newKey = collection.entries.keys()[0]
    if  db.lookup("citeKey", newKey) is not None:
        log.error("key %s already exists in DB", newKey)
        sys.exit(1)
    db.modBibtex(oldKey, collection)
    s.renameKey(oldKey, newKey)
    shutil.move(os.path.join(args.pdfDir, oldKey+".pdf"), os.path.join(args.pdfDir, newKey+".pdf"))


def cmd_tags(args):
    db = DB(args.dbFile)
    key = args.key
    tags = ["+" + t for t in args.add] + ["-" + t for t in args.remove]
    if not tags:
        print(db.getTags(key))
    else:
        db.modTags(key, tags)

def cmd_notes(args):
    s = TextSearch(args.indexDir)
    db = DB(args.dbFile)
    key = args.key

    bibs = db.lookup("citeKey", args.key)
    if bibs is None:
        log.error("Key %s not in database", args.key)
        sys.exit(1)

    if args.edit:
        note = s.getNote(key)
        if note is None:
            note = ""
        newNote = spawnEditor(note)
        if newNote != note:
            s.addNote(key, newNote)
        else:
            log.warning("not modified")
            sys.exit(0)
    elif args.remove:
        s.delNote(key)
    else:
        note = s.getNote(key)
        if note:
            print(formatBibEntries(bibs, [args.key], show_numbers=False))
            print(tc.colored("Notes", "green"))
            print(note)
        else:
            log.warning("No notes for %s", key)

import os, argparse
from . import *
from . Command import *
from . WwwApp import *

def main():
    if "VIRTUAL_ENV" in os.environ:
        dbDir = os.path.join(os.environ['VIRTUAL_ENV'], "sbdb")
    else:
        dbDir = os.path.join(os.path.expanduser("~"), "sbdb")

    class Dirs:
        pass

    dirs = Dirs()

    dirs.root = dbDir
    dirs.index = os.path.join(dbDir, "index")
    dirs.pdf = os.path.join(dbDir, "pdf")
    dirs.db = os.path.join(dbDir, "sqlite.dat")
    dirs.doicache = os.path.join(dbDir, "meta.pkl")
    dirs.pdfcache = os.path.join(dbDir, "text.pkl")

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="Bibliography database manipulation")

    subparsers = parser.add_subparsers(title='Commands')

    sp = subparsers.add_parser('init', help="Obliterate {} and initialize new database".format(dbDir))
    sp.set_defaults(func=dbInit)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('add', help="Add new pdf to database")
    sp.set_defaults(func=dbAdd)
    sp.set_defaults(dirs=dirs)
    sp.add_argument('file', metavar='PDFFILE', type=str)
    sp.add_argument("--doi", "-d", help="DOI", default=None)

    sp = subparsers.add_parser('search', help="Fulltext search")
    sp.add_argument('terms', type=str, nargs='+', help='Search string')
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--tag", "-G", help="Search for tags", action="store_true")
    g.add_argument("--text", "-t", help="Search body text", action="store_true")
    g.add_argument("--title", "-T", help="Search titles", action="store_true")
    g.add_argument("--year", "-Y", help="Search years", action="store_true")
    g.add_argument("--doi", "-D", help="Search dois", action="store_true")
    g.add_argument("--author", "-A", help="Search authors", action="store_true")
    g.add_argument("--editor", "-E", help="Search editor", action="store_true")
    g.add_argument("--journal", "-J", help="Search journals", action="store_true")
    g.add_argument("--cite-key", "-K", help="Search citation key", action="store_true")
    sp.add_argument("--no-context", action='store_true', help="Do not print context of full text match")
    sp.set_defaults(func=dbSearch)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('watch', help="Add new pdfs added to a dir")
    sp.add_argument('watchDir', type=str, help='Directory to watch')
    sp.set_defaults(func=dbWatch)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('www', help="Start webserver")
    sp.set_defaults(func=launchWWW)
    sp.set_defaults(dirs=dirs)
    
    sp = subparsers.add_parser('edit', help="Edit bibtex")
    sp.add_argument('key', type=str, help='Cite key')
    sp.set_defaults(func=dbEdit)
    sp.set_defaults(dirs=dirs)


    sp = subparsers.add_parser('bibtex', help="Get BibTeX")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", "-a", help="Dump all entries", action="store_true")
    g.add_argument("--key", "-k", metavar='CITE_KEY', help="Dump only the following cite keys", nargs='+', default=[])
    sp.set_defaults(func=dbBib)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('tags', help="Modify tags")
    sp.add_argument('key', type=str, help='Cite key')
    sp.add_argument("--add", "-a", help="Tags to add", nargs="+", default=[])
    sp.add_argument("--remove", "-r", help="Tags to remove", nargs="+", default=[])
    sp.set_defaults(func=dbModTags)
    sp.set_defaults(dirs=dirs)

    args = parser.parse_args()

    try:
        args.func(args)
    except AbortException:
        perror("Aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()

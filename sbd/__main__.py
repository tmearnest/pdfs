import os, argparse
from . import *
from . Command import *
from . WwwApp import *
from . Watch import *

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
    g.add_argument("--text", "-t", help="Search body text", action="store_true")
    g.add_argument("--title", "-T", help="Search titles", action="store_true")
    g.add_argument("--year", "-Y", help="Search years", action="store_true")
    g.add_argument("--doi", "-D", help="Search dois", action="store_true")
    g.add_argument("--author", "-A", help="Search authors", action="store_true")
    g.add_argument("--journal", "-J", help="Search journals", action="store_true")
    g.add_argument("--cite-key", "-K", help="Search citation key", action="store_true")
    sp.set_defaults(func=dbSearch)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('watch', help="Add new pdfs added to a dir")
    sp.add_argument('watchDir', type=str, help='Directory to watch')
    sp.set_defaults(func=dbWatch)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('www', help="Start webserver")
    sp.set_defaults(func=launchWWW)
    sp.set_defaults(dirs=dirs)

    sp = subparsers.add_parser('bibtex', help="Get BibTeX")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", "-a", help="Dump all entries", action="store_true")
    g.add_argument("--key", "-k", metavar='CITE_KEY', help="Dump only the following cite keys", nargs='+', default=[])
    sp.set_defaults(func=dbBib)
    sp.set_defaults(dirs=dirs)

    args = parser.parse_args()

    try:
        args.func(args)
    except AbortException:
        perror("Aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()

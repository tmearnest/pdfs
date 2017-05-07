import os, argparse
from . import *
from . Command import *

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
    sp.set_defaults(func=dbSearch)
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
    except AttributeError:
        parser.print_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()

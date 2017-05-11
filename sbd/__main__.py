import os
import sys
import argparse
from .Command import cmd_init, cmd_add, cmd_search, cmd_watch, cmd_edit, cmd_bibtex, cmd_tags, cmd_notes
from .CaptureDoi import AbortException
from .WwwApp import cmd_www
from .Cache import RequestCache
from .Logging import loggingSetup, log


def main():
    if "VIRTUAL_ENV" in os.environ:
        sbdbDir = os.path.join(os.environ['VIRTUAL_ENV'], "sbdb")
    else:
        sbdbDir = os.path.join(os.path.expanduser("~"), "sbdb")

    indexDir = os.path.join(sbdbDir, "index")
    pdfDir = os.path.join(sbdbDir, "pdf")
    dbFile = os.path.join(sbdbDir, "sqlite.dat")
    cacheFile = os.path.join(sbdbDir, "cache.pkl")

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="Bibliography database manipulation")

    parser.set_defaults(sbdbDir=sbdbDir)
    parser.set_defaults(indexDir=indexDir)
    parser.set_defaults(pdfDir=pdfDir)
    parser.set_defaults(dbFile=dbFile)
    parser.set_defaults(cacheFile=cacheFile)

    parser.add_argument("--logging-level", "-L",
                        help="Logging level: CRITICAL, ERROR, WARNING, INFO, DEBUG",
                        metavar="LEVEL", type=str, default="WARNING")

    subparsers = parser.add_subparsers(title='Commands')

    sp = subparsers.add_parser('init', help="Initialize new database at {}".format(sbdbDir))
    sp.add_argument("--force", help="Overwrite existing database", action='store_true')
    sp.set_defaults(func=cmd_init)

    sp = subparsers.add_parser('add', help="Add new pdf to database")
    sp.set_defaults(func=cmd_add)
    sp.add_argument('file', metavar='PDFFILE', type=str)
    sp.add_argument("--doi", "-d", help="DOI", default=None)

    sp = subparsers.add_parser('search', help="Fulltext search")
    sp.add_argument('terms', type=str, nargs='+', help='Search string')
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--tag", "-G", help="Search for tags", action="store_true")
    g.add_argument("--text", "-t", help="Search body text", action="store_true")
    g.add_argument("--note", "-n", help="Search notes", action="store_true")
    g.add_argument("--title", "-T", help="Search titles", action="store_true")
    g.add_argument("--year", "-Y", help="Search years", action="store_true")
    g.add_argument("--doi", "-D", help="Search dois", action="store_true")
    g.add_argument("--author", "-A", help="Search authors", action="store_true")
    g.add_argument("--editor", "-E", help="Search editor", action="store_true")
    g.add_argument("--journal", "-J", help="Search journals", action="store_true")
    g.add_argument("--cite-key", "-K", help="Search citation key", action="store_true")
    g.add_argument("--pmid", "-P", help="Search pubmed ID", action="store_true")
    g.add_argument("--abstract", "-B", help="Search abstract", action="store_true")
    sp.add_argument("--no-context", action='store_true', help="Do not print context of full text match")
    sp.set_defaults(func=cmd_search)

    sp = subparsers.add_parser('watch', help="Add new pdfs added to a dir")
    sp.add_argument('watchDir', type=str, help='Directory to watch')
    sp.set_defaults(func=cmd_watch)

    sp = subparsers.add_parser('www', help="Start webserver")
    sp.set_defaults(func=cmd_www)
    
    sp = subparsers.add_parser('edit', help="Edit bibtex")
    sp.add_argument('key', type=str, help='Cite key')
    sp.set_defaults(func=cmd_edit)

    sp = subparsers.add_parser('bibtex', help="Get BibTeX")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", "-a", help="Dump all entries", action="store_true")
    g.add_argument("--keys", "-k", metavar='CITE_KEY', help="Dump only the following cite keys", nargs='+', default=[])
    sp.set_defaults(func=cmd_bibtex)

    sp = subparsers.add_parser('tags', help="Modify tags")
    sp.add_argument('key', type=str, help='Cite key')
    sp.add_argument("--add", "-a", help="Tags to add", nargs="+", default=[])
    sp.add_argument("--remove", "-r", help="Tags to remove", nargs="+", default=[])
    sp.set_defaults(func=cmd_tags)

    sp = subparsers.add_parser('note', help="Add/modify notes")
    sp.add_argument('key', type=str, help='Cite key')
    g = sp.add_mutually_exclusive_group(required=False)
    g.add_argument("--edit", "-e", help="Add or edit note", action='store_true')
    g.add_argument("--remove", "-r", help="Delete note", action='store_true')
    sp.set_defaults(func=cmd_notes)

    args = parser.parse_args()
    loggingSetup(args.logging_level)

    try:
        RequestCache(cacheFile)
        args.func(args)
    except AbortException:
        log.error("Aborted")
        sys.exit(1)

if __name__ == "__main__":
    main()

import argparse, logging, shutil,os
from .Metadata import *
from .Db import *
from .Search import *

log = logging.getLogger(__name__)

def sbd():
    parser = argparse.ArgumentParser(description="Bibliography database manipulation")
    parser.add_argument('--initialize', help="Obliterate $HOME/.sbdb and initialize new database", action="store_true")
    parser.add_argument("--insert-with-doi", '-i', metavar="DOI PDFFILE", help="Insert new entry", nargs=2, type=str, default=None)
    parser.add_argument("--insert", '-I', metavar="PDFFILE", help="Insert new entry", type=str, default=None)
    parser.add_argument("--get-pdf", '-P', metavar="CITEKEY", help="Return filename of entry", type=str, default=None)
    parser.add_argument("--search-year", metavar="TERM", help="Return entries matching with year matching TERM", type=str, default=None)
    parser.add_argument("--search-content", metavar="TERM", help="Return entries with text matching TERM", type=str, default=None)
    parser.add_argument("--search-journal", metavar="TERM", help="Return entries with journal matching TERM", type=str, default=None)
    parser.add_argument("--search-author", metavar="TERM", help="Return entries with author matching TERM", type=str, default=None)
    parser.add_argument("--search-tag", metavar="TERM", help="Return entries with tag matching TERM", type=str, default=None)
    parser.add_argument("--tag", '-t', metavar="TERM", help="Return entries with tag matching TERM", type=str, action='append')
    parser.add_argument("--logging-level", "-L", dest='logLevel', 
                        help="Logging level: CRITICAL, ERROR, WARNING, INFO, DEBUG", metavar="LEVEL", type=str, default="INFO")

    args = parser.parse_args()

    level = getattr(logging, args.logLevel.upper(), None)
    if not isinstance(level, int):
        raise ValueError('Invalid log level: {}'.format(args.logLevel))
    logging.basicConfig(level=level, format='%(levelname)s) %(module)s - %(message)s',)

    dbDir = os.path.join(os.path.expanduser("~"), ".sbdb")
    searchDir = os.path.join(dbDir, 'index')
    pdfDir = os.path.join(dbDir,'pdf')
    dbFile = os.path.join(dbDir, "bib.db")


    if args.initialize:
        try:
            shutil.rmtree(dbDir)
        except FileNotFoundError:
            pass
        os.mkdir(dbDir)
        os.mkdir(pdfDir)
        os.mkdir(searchDir)
        BibDB.initialize(dbFile)
        Search.initialize(searchDir)
        exit()

    search = Search(searchDir)
    db = BibDB(dbFile)

    if args.insert_with_doi is not None or args.insert is not None:
        if args.insert is not None:
            fname = args.insert
            doi = guessDoi(args.insert)
            if doi is None:
                log.error("Cannot find a doi in the pdf text.")
                exit(1)
        else:
            doi, fname = args.insert_with_doi

        article = getMetaData(doi)
        article.tags = args.tag
        db.insertArticle(article)
        shutil.copy(fname, os.path.join(pdfDir, article.key + ".pdf"))
        text = getPdfText(fname)
        search.addDocument(article.key, text)
        log.info("Added {}".format(article.line()))
        exit()

    if args.get_pdf:
        article=db.getArticleByKey(args.get_pdf)
        print(os.path.join(pdfDir, article.key + ".pdf"))
        exit()



    articles = []
    if args.search_year:
        articles=db.getArticles(year=args.search_year)
    if args.search_content:
        articles = map(db.getArticleByKey, search.search(args.search_content))
    if args.search_journal:
        articles=db.getArticles(journal=args.search_journal)
    if args.search_author:
        articles=db.getArticles(author=args.search_author)
    if args.search_tag:
        articles=db.getArticles(tag=args.search_tag)

    for a in articles:
        print(a.line())





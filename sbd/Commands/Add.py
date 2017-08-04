from .Command import Command
from ..Database import Database
from ..Entry import Entry
from ..DoiExtract import entryFromUser, entryFromPdf
from ..AnsiBib import printWork

class Add(Command):
    command = 'add'
    help = "Import new PDF into repository"

    def set_args(self, subparser):
        subparser.add_argument('file', metavar='PDFFILE', type=str)
        subparser.add_argument("--doi", "-d", help="Specify DOI for metadata", type=str, default=None)
        subparser.add_argument("--supplementary", "-S", help="Supplemental files to attach", metavar="FILE", nargs="+", type=str, default=[])
        subparser.add_argument("--tags", "-t", help="Descriptive tags", nargs="+", type=str, metavar="TAG", default=[])

    def run(self, args):
        db = Database(dataDir=args.data_dir)
        if args.doi:
            entry = Entry.from_doi(args.doi)
            printWork(entry)
        else:
            entry = entryFromPdf(args.file) or entryFromUser(args.file)

        db.add(entry, args.file, args.supplementary, args.tags)
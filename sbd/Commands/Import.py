from .Command import Command
from ..Database import Database
from ..BaseWork import Work
from ..ExtractDoi import entryFromUser, entryFromPdf
from ..AnsiBib import printWork

class Import(Command):
    command = 'import'
    help = "Import entries from other database"

    def set_args(self, subparser):
        subparser.add_argument('src', metavar='SRC_REPO', type=str, help='Path to "articles" directory')
        subparser.add_argument("keys", help="Keys to import", nargs='+', type=str)

    def run(self, args):
        dbDest = Database(dataDir=args.data_dir)
        dbSrc = Database(dataDir=args.src)

        for k in args.keys:
            e = dbDest.copyFromDb(dbSrc, k)
            printWork(e)

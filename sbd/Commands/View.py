import subprocess
from .Command import Command
from ..Database import Database
from .. import UserException

class View(Command):
    command = 'view'
    help = "View article PDF and attachements"

    def set_args(self, subparser):
        subparser.add_argument('key', metavar='CITE_KEY', type=str)
        subparser.add_argument('label', nargs='?', metavar='NAME', default='PDF', type=str)

    def run(self, args):
        db = Database(dataDir=args.data_dir)

        try:
            e = next(x for x in db.works if x.key() == args.key)
        except StopIteration:
            raise UserException("Key {} not found".format(args.key))

        subprocess.Popen(['xdg-open', db.getFile(e, args.label)])

from .Command import Command
from ..Database import Database
from .. import UserException

class Attach(Command):
    command = 'attach'
    help = "Attach a supplementary file"

    def set_args(self, subparser):
        subparser.add_argument('key',  metavar='CITE_KEY', type=str)
        subparser.add_argument('file',  metavar='ATTACHMENT', type=str)
        subparser.add_argument('--name', '-n', metavar='NAME', type=str)

    def run(self, args):
        db = Database(dataDir=args.data_dir)
        try:
            e = next(x for x in db.works if x.key() == args.key)
        except StopIteration:
            raise UserException("Key {} not found".format(args.key))

        e.tags = sorted((set(e.tags) | set(args.add)) - set(args.remove))

        db.save()


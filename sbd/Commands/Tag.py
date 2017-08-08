from .Command import Command
from ..Database import Database
from ..Exceptions import UserException

class Tag(Command):
    command = 'tag'
    help = "Add/remove tags"

    def set_args(self, subparser):
        subparser.add_argument('key',  metavar='CITE_KEY', type=str)
        subparser.add_argument('--add', '-a', metavar='TAG', nargs='+', type=str, default=[])
        subparser.add_argument('--remove', '-r', metavar='TAG', nargs='+', type=str, default=[])

    def run(self, args):
        db = Database(dataDir=args.data_dir)
        try:
            e = next(x for x in db.works if x.key() == args.key)
        except StopIteration:
            raise UserException("Key {} not found".format(args.key))

        e.tags = sorted((set(e.tags) | set(args.add)) - set(args.remove))

        db.save()

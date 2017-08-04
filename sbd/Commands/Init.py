from .Command import Command
from ..Database import Database

class Init(Command):
    command = 'init'
    help = "Initialize new document repository"

    def set_args(self, subparser):
        subparser.add_argument("--force", help="Overwrite existing document repository", action='store_true')

    def run(self, args):
        Database.init(dataDir=args.data_dir, clobber=args.force)

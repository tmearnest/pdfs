import re
from .Command import Command
from .Completers import citekeyCompleter, tagCompleter, authorCompleter

class Bibtex(Command):
    command = 'bibtex'
    help = "Dump bibtex for keys"

    def set_args(self, subparser):
        subparser.add_argument("--title", "-t", metavar='REGEX', type=str, default=None)
        subparser.add_argument("--author", "-a", metavar='REGEX', type=str, default=None).completer = authorCompleter
        subparser.add_argument("--year", "-y", metavar='REGEX', type=str, default=None)
        subparser.add_argument("--tag", "-T", metavar='TAG', type=str, default=None).completer = tagCompleter
        subparser.add_argument('--key', '-k', metavar='REGEX', type=str).completer = citekeyCompleter
        subparser.add_argument('--all', '-A', action='store_true')

    def run(self, args):
        from ..Database import Database
        from ..TermOutput import msg

        db = Database(dataDir=args.data_dir)

        btexs = []
        search = any(getattr(args, k) for k in ['title', 'author', 'year', 'tag', 'key'])
        if args.all and search:
            msg.error("Search and the --all option are mutually exclusive")
        elif args.all:
            btexs = [x.bibtex for x in sorted(db.works, key=lambda x: x.key())]
        elif search:
            gen = iter(db.works)

            def match(g, f, r):
                if r:
                    return filter(lambda x: getattr(x, f)() and re.search(r, getattr(x, f)(), re.I), g)
                return g

            gen = match(gen, 'title', args.title)
            gen = match(gen, 'author', args.author)
            gen = match(gen, 'year', args.year)
            gen = match(gen, 'key', args.key)
            if args.tag:
                gen = filter(lambda x: args.tag in x.tags, gen)

            btexs = [x.bibtex for x in gen]
        else:
            msg.error("Must specify search arguments to list or --all")

        if btexs:
            print('\n'.join(btexs))

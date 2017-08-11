from .Command import Command
from ..AnsiBib import printWork
from ..TermOutput import msg, wrapWithColor, fg, bg, attr, stylize, printRule

class List(Command):
    command = 'search'
    help = "Search full text of PDF"

    def set_args(self, subparser):
        subparser.add_argument("query", nargs="+", type=str)

    def run(self, args):
        import re
        from ..Database import Database
        from ..AnsiBib import printBibliography

        db = Database(dataDir=args.data_dir)

        results = db.search(' '.join(args.query), formatter="ansi")
        for i,result in enumerate(results):
            printWork(result['entry'])
            print("Score: " + stylize("{: 4.3f}".format(result['score']), fg("yellow"), attr('bold')))
            print()
            for frag in result['frags']:
                printRule("page {:4d}".format(frag['page']), width=50, color=fg("blue")+attr('bold'))
                print(frag['frag'])

            if i < len(results)-1:
                printRule()

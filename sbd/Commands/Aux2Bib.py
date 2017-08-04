import re
from .Command import Command
from ..Database import Database
from ..Logging import log

class Aux2Bib(Command):
    command = 'aux2bib'
    help = "Read LaTeX .aux file and dump a .bib file contining all used citations"

    def set_args(self, subparser):
        subparser.add_argument('aux', metavar='AUX_FILE', type=str)
        subparser.add_argument('bib', metavar='BIB_FILE', type=str)

    def run(self, args):
        db = Database(dataDir=args.data_dir)
        auxKeys = set(re.findall(r"\\(?:bibcite|citation)\{([^}]+)\}", open(args.aux, "r").read()))
        auxKeys = sorted(x.strip() for x in auxKeys)

        btexs, missing = [], []

        for key in auxKeys:
            try:
                btexs.append(next(x.bibtex for x in db.works if x.key() == key))
            except StopIteration:
                missing.append(key)

        if btexs:
            with open(args.bib, "w") as bib:
                bib.write('\n'.join(btexs))

        if missing:
            log.warning("Citation keys missed: %s", str(missing))

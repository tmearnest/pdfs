import os
from .Command import Command
from ..Database import Database
from collections import Counter

class Info(Command):
    command = 'info'
    help = "Print information about current repository"

    def set_args(self, subparser):
        pass

    def run(self, args):
        db = Database(dataDir=args.data_dir)
        nworks = len(db.works)
        dataPath = db.dataDir

        dirSize = 0
        for f in os.listdir(dataPath):
            f = os.path.join(dataPath, f)
            if os.path.isfile(f):
                dirSize += os.path.getsize(f)

        tagCount = Counter()

        for e in db.works:
            tagCount.update(e.tags)

        fields = [("Data path", dataPath),
                  ("Size",      "{:.3f} MB".format(dirSize/(1<<20))),
                  ("Works",      str(nworks))]


        w = max(len(x) for x in tagCount)
        w = max(1+w, 12)

        print('\n'.join("{:<12s}{}".format(*x) for x in fields))
        print("Tags:")
        for t,c in sorted(tagCount.items(), key=lambda x: -x[1]):
            print("{t:>{w}} {c:>3d}".format(t=t,c=c,w=w))

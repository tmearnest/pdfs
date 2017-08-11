from .BibFormatter import BibFormatter
from .TermOutput import msg, wrapWithColor, fg, bg, attr, stylize

def _co(x, c):
    if x:
        return stylize(x,c)

class AnsiBib(BibFormatter):
    def tag(self, t):
        return _co(t, fg('red') + attr('bold'))

    def attachment(self, a):
        return _co(a, fg('cyan'))

    def key(self):
        return _co(super().key(), fg('green'))

    def index(self):
        return _co(super().index(), fg('white') + attr('bold'))

    def year(self):
        return _co(super().year(), fg('magenta'))

    def booktitle(self):
        return _co(super().booktitle(), fg('cyan') + attr('bold'))

    def volume(self):
        return _co(super().volume(), fg('yellow'))

    def journal(self):
        return _co(super().journal(), fg('cyan') + attr('bold'))

    def doi(self):
        return _co("doi:"+super().doi(), fg('blue'))

    def fmt(self, *args, **kwargs):
        f = super().fmt(*args, **kwargs)
        return wrapWithColor(f)

def printBibliography(works):
    for i,w in enumerate(works):
        printWork(w, index=i+1)

def printWork(work, index=None):
    print(AnsiBib(work, index).fmt())

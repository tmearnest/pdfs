import termcolor as tc
import shutil
import re
from .DisplayBib import DisplayBib

_ansiRe = re.compile(r"((?:\x1b\[[0-9;]+?m)+)")
_wsRe = re.compile(r"(\s+)")

def _clr(s, c, attrs=None):
    if s:
        return  tc.colored(s, c, attrs=attrs)

class AnsiBib(DisplayBib):
    def tag(self, t):
        return tc.colored(t, 'red', attrs=['bold'])

    def attachment(self, a):
        return tc.colored(a, 'cyan')

    def key(self):
        return _clr(super().key(), 'green')

    def index(self):
        return _clr(super().index(), 'white', attrs=['bold'])

    def year(self):
        return _clr(super().year(), 'magenta')

    def booktitle(self):
        return _clr(super().booktitle(), 'cyan', attrs=['bold'])

    def volume(self):
        return _clr(super().volume(), 'yellow')

    def journal(self):
        return _clr(super().journal(), 'cyan', attrs=['bold'])

    def doi(self):
        return _clr("doi:"+super().doi(), 'blue')

    def fmt(self, *args, **kwargs):
        f = super().fmt(*args, **kwargs)
        return wrapWithColor(f)


def wrapWithColor(s, width=None, firstIndent=0,indent=3):
    if not width:
        width = min(120, shutil.get_terminal_size()[0])

    splt =  sum(([y for y in _wsRe.split(x) if len(y)>0] for x in _ansiRe.split(s)), [])

    lines = []
    line = " "*firstIndent
    lineSize = firstIndent
    lastAnsi = '\x1b[0m'

    for frag in splt:
        if frag[0] == '\x1b':
            fragSize = 0
            lastAnsi = frag
        else:
            fragSize = len(frag)

        if fragSize + lineSize > width:
            lines.append(line)
            line = " "*indent + lastAnsi + frag.strip()
            lineSize = len(frag.strip()) + indent
        else:
            line += frag
            lineSize += fragSize

    if line.strip():
        lines.append(line)

    return "\n".join(lines) + "\n"

def printBibliography(works):
    for i,w in enumerate(works):
        printWork(w, index=i+1)

def printWork(work, index=None):
    print(work.format(AnsiBib, index=index))

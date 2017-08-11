from .Bases import Singleton
from colored import stylize, fg, bg, attr
import sys
import shutil
import re

_ansiRe = re.compile(r"((?:\x1b\[[0-9;]+?m)+)")
_wsRe = re.compile(r"(\s+)")

def printRule(label='', *, ch='-', width=None, color=None):
    if not color:
        color=fg("white") +  attr('dim')
    if not width:
        width = max(1, shutil.get_terminal_size()[0]-4)
    if label:
        w = width - len(label) - 2
        lwidth = w//2 
        rwidth = w-lwidth
        lwidth, rwidth = max(0,lwidth), max(0,rwidth)
        print(stylize(ch*lwidth + " " + label + " " + ch*rwidth, color))
    else:
        print(stylize(ch*width, color))

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


class TermOutput(metaclass=Singleton):
    @property
    def width(self):
        return shutil.get_terminal_size()[0]
    def __init__(self):
        self.setup()

    def setup(self, *,level='info', term=None):
        l = level.lower()
        if l == 'debug':
            self.logLevel = 4
        elif l == 'info':
            self.logLevel = 3
        elif l == 'warning':
            self.logLevel = 2
        elif l == 'error':
            self.logLevel = 1
        elif l == 'critical':
            self.logLevel = 0
        else:
            raise RuntimeError("Invalid log level")
        if term is not None:
            self.isTermE = term
            self.isTermO = term
        else:
            self.isTermE = sys.stderr.isatty()
            self.isTermO = sys.stdout.isatty()

        if self.isTermE:
            self.icos = [stylize("*", fg("white") + bg("red") + attr('bold')),
                         stylize("*", fg("red") + attr('bold')),
                         stylize("*", fg("yellow") + attr('bold')),
                         stylize("*", fg("cyan")),
                         stylize("*", fg("white") + attr('dim'))]
        else:
            self.icos = ["CRIT", "ERR ", "WARN", "INFO", "DBUG"]

    def _plog(self, lvl, msg, args):
        if self.logLevel >= lvl:
            print(self.icos[lvl], msg % args, file=sys.stderr)

    def debug(self, msg, *args): self._plog(4, msg, args)
    def info(self, msg, *args): self._plog(3, msg, args)
    def warning(self, msg, *args): self._plog(2, msg, args)
    def error(self, msg, *args): self._plog(1, msg, args)
    def critical(self, msg, *args): self._plog(0, msg, args)

    def __call__(self, *args, **kwargs):
        return print(*args, **kwargs)

msg = TermOutput()

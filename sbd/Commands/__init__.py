from .Add import Add
from .Aux2Bib import Aux2Bib
from .Bibtex import Bibtex
from .Command import Command
from .Edit import Edit
from .Init import Init
from .List import List
from .View import View
from .WatchDir import WatchDir
from .WWW import WWW

def getCommandTypes():
    types = []
    for v in globals().values():
        if isinstance(v, type) and issubclass(v, Command) and v is not Command:
            types.append(v)

    return types

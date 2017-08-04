from .Command import Command
from .Init import Init
from .Add import Add
from .List import List
from .WWW import WWW
from .WatchDir import WatchDir
from .Aux2Bib import Aux2Bib
from .Edit import Edit

def getCommandTypes():
    types = []
    for v in globals().values():
        if isinstance(v, type) and issubclass(v, Command) and v is not Command:
            types.append(v)

    return types

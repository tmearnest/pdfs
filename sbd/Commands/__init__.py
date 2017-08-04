from .Init import *
from .Add import *
from .List import *
from .WWW import *
from .WatchDir import *
from .Aux2Bib import *
from .Edit import *

def getCommandTypes():
    types = []
    for v in globals().values():
        if isinstance(v, type) and issubclass(v, Command) and v is not Command:
            types.append(v)

    return types

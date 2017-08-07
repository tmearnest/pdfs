import os
import sys
import argparse
from . import AbortException, UserException, EntryExistsException
from .Database import Database
from .Logging import log, loggingSetup
from .Commands import registerCommands
from .Cache import RequestCache

def main():
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="Bibliography database manipulation")

    parser.add_argument("--debug", action="store_true")

    parser.add_argument("--logging-level", "-L",
                        help="Logging level: CRITICAL, ERROR, WARNING, INFO, DEBUG",
                        metavar="LEVEL", type=str, default="WARNING")

    parser.add_argument("--data-dir", help="Path to articles directory", type=str, default=None)

    subparsers = parser.add_subparsers(title='Commands')

    registerCommands(subparsers)

    args = parser.parse_args()
    if args.debug:
        loggingSetup("DEBUG")
    else:
        loggingSetup(args.logging_level)

    ddir = Database.getDataDir(dataDir=args.data_dir)
    if ddir:
        RequestCache(os.path.join(ddir, ".cache.pkl"))

    try:
        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_usage()
    except UserException as e:
        log.error("Error: %s", e)
        if args.debug:
            raise
        else:
            sys.exit(1)
    except AbortException:
        log.error("Aborted")
        if args.debug:
            raise
        else:
            sys.exit(1)
    except EntryExistsException as e:
        log.error(str(e))
        if args.debug:
            raise
        else:
            sys.exit(1)
    except:
        t,v,_ = sys.exc_info()
        log.critical("Unhandled exception: %s(%s)", t.__name__, v)
        if args.debug:
            raise
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()

import os.path
import inotify.adapters
from pdfminer.pdfparser import PDFSyntaxError
from .Command import Command
from ..Database import Database
from ..Logging import log
from ..ExtractDoi import entryFromUser, entryFromPdf
from ..Exceptions import WorkExistsException, AbortException

class WatchDir(Command):
    command = 'watch'
    help = "Watch a directory for new pdf files to add"

    def set_args(self, subparser):
        subparser.add_argument('dir', metavar='DIRECTORY', type=str)

    def run(self, args):
        wd = os.path.abspath(args.dir)
        inot = inotify.adapters.Inotify()
        inot.add_watch(wd.encode())
        log.info("Watching %s for new pdf files...", wd)

        try:
            createdFiles = set()
            for event in inot.event_gen():
                if event is not None:
                    _, type_names, _, filename = event
                    log.debug("INOTIFY: %s (%s)", filename.encode(), ', '.join(type_names))
                    if 'IN_CREATE' in type_names:
                        f = filename.decode("utf-8")
                        if f.lower().endswith(".pdf") and f[0] != '.':
                            createdFiles.add(filename)
                    elif 'IN_CLOSE_WRITE' in type_names and filename in createdFiles:
                        createdFiles.remove(filename)
                        try:
                            newFile = filename.decode("utf-8")
                            newFilePath = os.path.join(wd, newFile)
                            db = Database(dataDir=args.data_dir)
                            k = db.find(pdfFname=newFilePath)
                            if k:
                                raise WorkExistsException("new file {} exists in database as {}".format(newFile, k))
                            else:
                                log.info("new file: %s", newFile)
                                entry = entryFromPdf(newFilePath) or entryFromUser(newFilePath)
                                db.add(entry, newFilePath, [], [])
                        except WorkExistsException as e:
                            log.warning(str(e))
                        except AbortException:
                            log.warning("PDF import aborted")
                        except PDFSyntaxError:
                            log.warning("file %s seems broken", newFile)
        except KeyboardInterrupt:
            pass
        finally:
            inot.remove_watch(wd)

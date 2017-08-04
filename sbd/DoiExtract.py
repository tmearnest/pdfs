import re
import os
from . import *
from .Prompt import promptOptions, promptString
from .Logging import log
from .Entry import Entry
from .AnsiBib import printBibliography, printWork
from .ReadPdf import getPdfTxt

_doiRegexStr= re.compile(r'10[.][0-9]{4,}[^\s"/<>]*/[^\s"<>]+')

def _chopPeriod(x):
    if x[-1] == '.':
        return x[:-1]
    return x

def extractDois(fname):
    pdfData = getPdfTxt(fname)
    dois = [_chopPeriod(x.lower()) for x in _doiRegexStr.findall(pdfData)]
    seen = set()
    return [x for x in dois if not (x in seen or seen.add(x))]

def entryFromPdf(fname):
    dois = extractDois(fname)
    maxChoices = 5

    def chunker():
        lst = []
        for doi in dois:
            obj = Entry.from_doi(doi)
            if obj is not None:
                lst.append(obj)
            if len(lst)==maxChoices:
                yield lst
                lst = []
        if lst:
            yield lst
            
    showMsg = True
    for chunkId, bibChunk in enumerate(chunker()):
        if len(bibChunk) == 1 and chunkId == 0:
            printWork(bibChunk[0])
            return bibChunk[0]
        if showMsg:
            print("Found {} putative DOIs in {}:\n".format(len(dois), fname) )
            showMsg = False

        printBibliography(bibChunk)

        choice = None
        while choice is None:
            try:
                choice = promptOptions("Choose reference for "+os.path.basename(fname),
                                       [str(x+1) for x in range(len(bibChunk))] + ["n", "q"])

                if choice.lower() == 'q':
                    raise AbortException
                if choice.lower() == 'n':
                    choice = None
                    break

                choice = int(choice)
                if not (1<= choice <= len(bibChunk)):
                    raise ValueError
                else:
                    print()
                    return bibChunk[choice-1]
            except ValueError:
                log.warning("Invalid response")
                choice = None
    return None


def entryFromUser(fname):
    while True:
        doi = promptString("Enter DOI for {} ".format(os.path.basename(fname)))
        if doi.lower() == 'q':
            raise AbortException
        bibData = Entry.from_doi(doi)
        if bibData is None:
            log.warning("Doi not found.")
            continue

        printWork(bibData)

        response = promptOptions("OK" , ['y','n','q'], default='y')

        if response == 'q':
            raise AbortException
        elif response == 'y':
            return bibData

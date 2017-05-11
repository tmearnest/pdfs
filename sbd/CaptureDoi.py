import re
import os
from .Prompt import promptOptions, promptString

from .Logging import log
from .BibFormat import formatBibEntries, concatBibliography

class AbortException(Exception):
    pass

def extractDois(txt):
    dois =  [x.group(0).lower() for x in re.finditer(r'(10\.\d{4,9}/[-._/:A-Za-z0-9]+[A-Za-z0-9])',txt)]
    seen = set()
    return [x for x in dois if not (x in seen or seen.add(x))]

def selectDoi(txt, fname, doiLookup):
    dois = extractDois(txt)
    maxChoices = 5

    def chunker():
        lst = []
        for doi in dois:
            obj = doiLookup(doi)
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
            return bibChunk[0]
        if showMsg:
            print("Found {} putative DOIs in {}:\n".format(len(dois), fname) )
            showMsg = False

        bibs, keys = [], []
        for bib in bibChunk:
            k = bib.entries.keys()[0]
            bibs.append(bib)
            keys.append(k)
        print(formatBibEntries(concatBibliography(bibs), keys))

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


def doiEntry(fname, doiLookup):
    while True:
        doi = promptString("Enter DOI for {} ".format(os.path.basename(fname)))
        if doi.lower() == 'q':
            raise AbortException
        bibData = doiLookup(doi)
        if bibData is None:
            log.warning("Doi not found.")
            continue

        print(formatBibEntries(bibData, list(bibData.entries.keys()), show_numbers=False))

        response = promptOptions("OK" , ['y','n','q'], default='y')

        if response == 'q':
            raise AbortException
        elif response == 'y':
            return bibData

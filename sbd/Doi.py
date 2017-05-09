from pybtex.database import parse_string, BibliographyData
from pybtex.style.formatting.unsrt import Style as Unsrt
import re, io, os
import textwrap

from . import *

class AbortException(Exception):
    pass

from pybtex.backends import BaseBackend


class ANSIBackend(BaseBackend):
    ansi_no_number = False
    ansi_no_key = False
    default_suffix = '.txt'
    symbols = {
        'ndash': u'-',
        'newblock': u' ',
        'nbsp': u' '
    }

    def format_tag(self, tag_name, text):
        return tc.colored(text, "cyan")

    def format_href(self, url, text):
        return tc.colored(text, "blue")

    def write_entry(self, key, label, text):
        ss = []

        if not self.ansi_no_number:
            ss.append(tc.colored(label,"yellow"))
        if not self.ansi_no_key:
            ss.append(tc.colored(key,"blue"))
        s = '/'.join(ss)
        if len(s) > 0:
            self.output('[' + s + ']\n')
        self.output(textwrap.fill(text, width=80, initial_indent="   ", subsequent_indent="   " ))
        self.output("\n\n")


def prompt(txt, options=None, validate=None):
    pstr = tc.colored(txt, 'green')
    if options is not None:
        pstr += " ["
        pstr += tc.colored(options, "blue", attrs=['bold'])
        pstr += "]"
    pstr += tc.colored("> ", 'white', attrs=['bold'])

    if options is not None and validate is None:
        validate = lambda x: x.lower() in options
    
    if validate is None:
        validate = lambda x: True
        

    while True:
        v = input(pstr).strip(' \t\n\r')
        if validate(v):
            return v
        else:
            perror("Invalid input")


def rekey(bib, citekey):
    ent = bib.entries[bib.entries.keys()[0]]
    ent.key = citekey
    bib2 = BibliographicData()
    bib2.add_entry(citekey, ent)
    return bib2


def extractDois(txt):
    dois =  [x.group(0).lower() for x in re.finditer(r'(10\.\d{4,9}/[-._/:A-Za-z0-9]+[A-Za-z0-9])',txt)]
    seen = set()
    return [x for x in dois if not (x in seen or seen.add(x))]


def formatBibEntries(bdb, keys, show_numbers=True, show_keys=True):
    style = Unsrt()
    formatted_bibliography = style.format_bibliography(bdb, keys)
    f = io.StringIO()
    be = ANSIBackend(None)
    be.ansi_no_number = not show_numbers
    be.ansi_no_key = not show_keys
    be.write_to_stream(formatted_bibliography, f)
    return f.getvalue()

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
        if len(lst) > 0:
            yield lst
            
    showMsg = True
    for chunkId, bibChunk in enumerate(chunker()):
        if len(bibChunk) == 1 and chunkId == 0:
            return bibChunk[0]
        if showMsg:
            print("Found {} putative DOIs in {}:\n".format(len(dois), fname) )
            showMsg = False

        bibs, keys = BibliographyData(), []
        for i,bib in enumerate(bibChunk):
            k = bib.entries.keys()[0]
            bibs.add_entry(k, bib.entries[k])
            keys.append(k)
        print(formatBibEntries(bibs, keys))

        choice = None
        while choice is None:
            try:
                choice = prompt("Choose correct reference for " + os.path.basename(fname), "".join(str(x+1) for x in range(len(bibChunk))) + "n" + "q")

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
                perror("Invalid response")
                choice = None
    return None


def doiEntry(fname, doiLookup):
    while True:
        doi = prompt("Enter DOI for {} ".format(os.path.basename(fname)))

        if len(doi) == 0:
            raise AbortException
        else:
            bibData = doiLookup(doi)
            if bibData is None:
                pinfo("Doi not found.")
                continue

            print(formatBibEntries(bibData, list(bibData.entries.keys()), show_numbers=False))

            response = prompt("OK" , "yn")
            if response.lower() == 'y':
                return bibData


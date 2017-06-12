import io
import itertools
import textwrap
import termcolor as tc
from pybtex.database import BibliographyData
from pybtex.backends import BaseBackend
from pybtex.backends.html import Backend as OldHtmlBackend
from pybtex.style.formatting.unsrt import Style as Unsrt

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
        if s:
            self.output('[' + s + ']\n')
        self.output(textwrap.fill(text, width=80, initial_indent="   ", subsequent_indent="   " ))
        self.output("\n\n")

def formatBibEntries(bdb, keys, show_numbers=True, show_keys=True):
    style = Unsrt()
    formatted_bibliography = style.format_bibliography(bdb, keys)
    f = io.StringIO()
    be = ANSIBackend(None)
    be.ansi_no_number = not show_numbers
    be.ansi_no_key = not show_keys
    be.write_to_stream(formatted_bibliography, f)
    return f.getvalue().strip()


def bibSingleEntry(bib):
    return bib.entries[bib.entries.keys()[0]]

def rekey(bib, citekey):
    ent = bibSingleEntry(bib)
    ent.key = citekey
    bib2 = BibliographyData()
    bib2.add_entry(citekey, ent)
    return bib2

def concatBibliography(bibs):
    db = BibliographyData()
    keys = set()
    for bib in bibs:
        for key,entry in bib.entries.items():
            if key in keys:
                for i in itertools.count():
                    newKey = "{}.{:04d}".format(key,i)
                    if newKey not in keys:
                        break
                key = newKey
            db.add_entry(key, entry)
            keys.add(key)
    return db

class HtmlBackend(OldHtmlBackend):
    def write_entry(self, key, label, text):
        self.output('<dt><a href="/pdf/{key}.pdf" target="_blank">{key}</a></dt>\n'.format(key=key))
        self.output('<dd>{text}</dd>\n'.format(text=text))

class HtmlFragmentBackend(OldHtmlBackend):
    def write_entry(self, key, label, text):
        self.output(text)
    def write_prologue(self):
        pass
    def write_epilogue(self):
        pass

def formatBibEntriesHTML(bdb, keys, fragment=False):
    style = Unsrt()
    formatted_bibliography = style.format_bibliography(bdb, keys)
    f = io.StringIO()
    if fragment:
        be = HtmlFragmentBackend(None)
    else:
        be = HtmlBackend(None)
    be.write_to_stream(formatted_bibliography, f)
    return f.getvalue()

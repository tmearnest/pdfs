import requests
import pickle
import ftfy
from pybtex.database import parse_string, BibliographyData, Entry, Person
import re
from unidecode import unidecode
from . import *
import pypandoc

class DoiLookup:
    def __init__(self, cacheFile):
        self.cacheFile = cacheFile
        try:
            self.cache = pickle.load(open(self.cacheFile,"rb"))
        except FileNotFoundError:
            self.cache = {}

    def __call__(self, doi):
        if doi in self.cache:
            pinfo("Doi cache hit")
            return _parseBibtex(self.cache[doi])
        else:
            pinfo("Doi cache miss")
            bibtex = self._lookup(doi)
            self.cache[doi] = bibtex
            pickle.dump(self.cache, open(self.cacheFile,"wb"))
            return _parseBibtex(bibtex)

    @staticmethod
    def _lookup(doi):
        url = 'http://dx.doi.org/{}'.format(doi)
        headers = {'accept': 'application/x-bibtex'}
        r = requests.get(url, headers=headers)
        return r.text



def _parseBibtex(bibTex):
    txt = '\n'.join(x for x in bibTex.splitlines() if not re.search(r"^\s*(link|url)\s*=",x, re.I))
    coll = parse_string(txt, "bibtex")
    db = BibliographyData()
    empty = True
    for k,e in coll.entries.items():
        keyPerson = e.persons.get('author') or e.persons.get('editor')
        if keyPerson is None:
            return None
        firstAuthor = "".join(keyPerson[0].last_names)
        year = e.fields['year']
        title = e.fields.get('title') or e.fields.get("booktitle") 
        if title is None:
            return None

        suffix = ''
        for word in title.split(' '):
            for ch in word:
                if ch.isalnum():
                    suffix += ch
                    break
            if len(suffix) == 3:
                break
        rawKey = '{}{}{}'.format(firstAuthor.replace('-', ''), year, suffix.lower())
        citekey = unidecode(pypandoc.convert_text(ftfy.fix_text(rawKey), 'plain', format='latex').strip())

        db.add_entry(citekey, e)
        empty = False

    return None if empty else db

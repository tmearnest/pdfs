import requests
import pickle
import ftfy
from pybtex.database import parse_string, BibliographyData, Entry, Person
import re
from unidecode import unidecode
from .Pandoc import detex
from . import *

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
        citekey = unidecode(detex(ftfy.fix_text('{}{}{}'.format(firstAuthor, year, suffix.lower()))))
        db.add_entry(citekey, e)
        empty = False

    return None if empty else db

# def _parseBibtex(bibTex):
#     txt = '\n'.join(x for x in bibTex.splitlines() if not re.search(r"^\s*(link|url)\s*=",x, re.I))
#     coll = parse_string(txt, "bibtex")
#     db = BibliographyData()
#     empty = True
#     for k,e in coll.entries.items():
#         e2 = Entry(e.type)
#         for ptype, ps in e.persons.items():
#             ps2 = []
#             for p in ps:
#                 name = " ".join([" ".join(p.first_names), " ".join(p.middle_names), " ".join(p.last_names)])
#                 newName = _translateText(name)
#                 if newName != name:
#                     pinfo("{} Name: {} -> {}".format(ptype, name,newName))
#                 ps2.append(Person(newName))
#             e2.persons[ptype] = ps2

#         for k,v in e.fields.items():
#             v2 = _translateText(v)
#             if v2 != v:
#                 pinfo("{}: {} -> {}".format(k, v, v2))
#             e2.fields[k] = v2

#         keyPerson = e2.persons.get('author') or e2.persons.get('editor')
#         if keyPerson is None:
#             return None
#         firstAuthor = "".join(keyPerson[0].last_names)
#         year = e2.fields['year']
#         title = e.fields.get('title') or e.fields.get("booktitle") 
#         if title is None:
#             return None

#         suffix = ''
#         for word in title.split(' '):
#             for ch in word:
#                 if ch.isalnum():
#                     suffix += ch
#                     break
#             if len(suffix) == 3:
#                 break
#         citekey = unidecode('{}{}{}'.format(firstAuthor, year, suffix.lower()))
#         db.add_entry(citekey, e2)
#         empty = False

#     return None if empty else db

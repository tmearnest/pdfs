import xml.etree.ElementTree as etree
import requests
import ftfy
from pybtex.database import parse_string, BibliographyData
import re
from unidecode import unidecode
import pypandoc
from .Cache import cachedRequest
from .Logging import log


@cachedRequest("DOI")
def _doiLookup(doi):
    url = 'http://dx.doi.org/{}'.format(doi)
    headers = {'accept': 'application/x-bibtex'}
    return requests.get(url, headers=headers).text


def doiLookup(doi):
    bibTex = _doiLookup(doi)
    txt = '\n'.join(x for x in bibTex.splitlines() if not re.search(r"^\s*(link|url)\s*=",x, re.I))
    coll = parse_string(txt, "bibtex")
    db = BibliographyData()
    empty = True
    for e in coll.entries.values():
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
        citekey = '{}{}{}'.format(firstAuthor, year, suffix.lower())
        citekey = unidecode(pypandoc.convert_text(ftfy.fix_text(citekey), 'plain', format='latex').strip())
        citekey = re.sub('[^A-Za-z0-9]', '', citekey)

        db.add_entry(citekey, e)
        empty = False

    return None if empty else db


@cachedRequest("Esearch")
def _pmidRequest(doi):
    r = requests.get("http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                     params=dict(tool='sbd',
                                 email='tylere@rne.st',
                                 term=doi))
    return r.text


@cachedRequest("Efetch")
def _pmAbsRequest(pmid):
    r = requests.get('http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?',
                     params=dict(tool='sbd',
                                 email='tylere@rne.st',
                                 db='pubmed',
                                 retmode='XML',
                                 rettype='abstract',
                                 id=pmid))
    return r.text


def pmidAbstractLookup(doi):
    try:
        pmid = (etree.fromstring(_pmidRequest(doi))
                     .find("IdList")
                     .find("Id").text)
    except AttributeError:
        return None, None

    try:
        abstract = (etree.fromstring(_pmAbsRequest(pmid))
                         .find("PubmedArticle")
                         .find("MedlineCitation")
                         .find("Article")
                         .find("Abstract")
                         .find("AbstractText").text)
    except AttributeError:
        return pmid, None

    return pmid, abstract

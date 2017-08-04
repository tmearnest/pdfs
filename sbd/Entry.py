import unicodedata
import re
from .unimap import separator_map, char_map
from .Logging import log
from .Crossref import crossrefLookup
import textwrap

_regularizeWsRe = re.compile(r"\s+")
def _regularizeWs(x):
    return _regularizeWsRe.sub(' ', x)

def _mergeDicts(*dicts):
    new_dict = dict()
    for d in reversed(dicts):
        for k,v in d.items():
            new_dict[k] = v
    return new_dict

def _parsePerson(au):
    if 'given' in au:
        return au['family'] + ', ' + au['given']
    ns = au['family'].split(' ')
    return ns[-1] + ", " + ' '.join(ns[:-1])

def _unicodeNorm(x):
    return unicodedata.normalize("NFKD", x).encode('ascii', 'ignore').decode()

def _unicode2tex_sep(xs):
    return ''.join(map(lambda x:separator_map.get(x,x), xs)).strip()

def _unicode2tex_chr(xs):
    return ''.join(map(lambda x:char_map.get(x,x), xs)).strip()

def _unicode2tex(xs):
    return _unicode2tex_chr(_unicode2tex_sep(xs))

def _caseDist(xs):
    n = len(xs)
    l = sum(1 for x in xs if x.islower())
    u = sum(1 for x in xs if x.isupper())
    if len(xs) > 1:
        l1 = sum(1 for x in xs[1:] if x.islower())
        tcase = n-l1 == 1 and xs[0].isupper()
    else:
        tcase = False
    return n, l, u, tcase

def _btexPreserveCaps(xs):
    letters = re.sub('[^a-zA-Z]+', '', xs)
    n, l, u, _ = _caseDist(letters)
    if n==l or n==u:
        return xs.title()
    tokens = re.split(r"((?:(?:\)|\])|(?:\?|!|\.|\,|;|:)|(?:\s+|-+)|(?:\(|\[))+)", xs)
    words = tokens[0::2]
    seps = tokens[1::2]
    seps.append('')
    escaped=''

    for w,s in zip(words,seps):
        n, l, u, tcase = _caseDist(w)
        w = _unicode2tex_chr(w)
        if n>1 and not tcase and l!=n and u>0:
            escaped+="{{{}}}{}".format(w,s)
        else:
            escaped+="{}{}".format(w,s)
    return escaped

def _bibKeyQuote(k,v):
    if k == 'month':
        st = v
    elif k=='pages':
        st =  "{" + re.sub('-+', '--', _unicode2tex_sep(v)) + "}"
    elif k in ['title', 'booktitle', 'journal', 'publisher']:
        st =  "{" + _btexPreserveCaps(_unicode2tex_sep(v)) + "}"
    else:
        try:
            st =  str(int(v))
        except ValueError:
            st =  "{" + _unicode2tex(v) + "}"
    return _regularizeWs(st)

class EntryMeta(type):
    def __new__(cls, name, parents, namespace):
        allFields = ["author", "title", "booktitle", "series", "journal", "edition", 
                      "editor", "institution", "organization", "publisher", "school", 
                      "address", "chapter", "volume", "number", "pages", "year", 
                      "month", "doi"]
        namespace['_allFields'] = allFields

        reqClsFields = dict(_crossrefTypes=list, _reqFields=list, _optFields=list, btexType=str)
        if parents:
            for attr,tp in reqClsFields.items():
                if attr not in namespace or not isinstance(namespace[attr], tp):
                    raise AttributeError("EntryMeta classes must have a {} attribute called {}".format(tp.__name__, attr))

        if parents:
            sc = dir(parents[0])
        else:
            sc = []

        for field in allFields:
            dField  = "_dict_" + field

            if dField not in namespace and dField not in sc:
                namespace[dField] = lambda s: dict()

            namespace[field] = lambda s, field=field: getattr(s, "_dict_"+field)().get(field)

        if parents:
            ts = namespace['_optFields'] + namespace['_reqFields']

            if 'authorOrEditor' in ts:
                del ts[ts.index('authorOrEditor')]
                ts.append('author')
                ts.append('editor')

            if 'volumeOrNumber' in ts:
                del ts[ts.index('volumeOrNumber')]
                ts.append('volume')
                ts.append('number')

            okFields = set(ts)

            for field in allFields:
                if field not in okFields:
                    namespace[field] = lambda s: None

        newCls = type.__new__(cls, name, parents, namespace)

        if not hasattr(cls, '_typeMap'):
            cls._typeMap = dict()
        else:
            for x in newCls._crossrefTypes:
                cls._typeMap[x] = newCls

        return newCls


class Entry(metaclass=EntryMeta):
    def key(self):
        return self._citeKey

    def set_key(self, newKey):
        if hasattr(self, "bibtex"):
            self.bibtex = self.bibtex.replace(self._citeKey, newKey)
        self._citeKey = newKey

    @classmethod
    def from_doi(cls, doi):
        meta = crossrefLookup(doi)
        if meta:
            return cls.from_metadata(meta)

    @classmethod
    def from_metadata(cls, meta):
        return cls.from_db(meta=meta)

    @classmethod
    def from_db(cls, **kwargs):
        tp = kwargs['meta']['type']
        try:
            return cls._typeMap[tp](**kwargs)
        except KeyError:
            raise ValueError("Unrecognized work type: "+tp)

    def toDict(self):
        return dict(meta=self.meta, citeKey=self.key(), tags=self.tags, 
                    files=self.files, fileLabels=self.fileLabels, 
                    md5s=self.md5s, bibtex=self.bibtex)

    def __init__(self, meta, fileLabels=None, citeKey=None, tags=None, files=None, md5s=None, bibtex=None):
        if type(self) == Entry:
            raise RuntimeError("Do not instantiate {} directly".format(type(self)))
        self.meta = meta
        self.tags = tags or list()
        self.files = files or list()
        self.md5s = md5s or list()
        self.fileLabels = fileLabels or list()
        self._citeKey = citeKey or self._makeCiteKey()
        self.bibtex = bibtex or self.bibtexFromMetadata()

    def bibtexFromMetadata(self):
        btexDict = dict()

        for field in self._reqFields:
            d = getattr(self, "_dict_"+field)()
            if d:
                btexDict = _mergeDicts(btexDict, d)
            else:
                log.debug("%s missing %s", self.meta['DOI'],field)

        for field in self._optFields:
            d = getattr(self, "_dict_"+field)()
            if d:
                btexDict = _mergeDicts(btexDict, d)

        bt = "@{type}{{{key},\n{keys}\n}}\n"
        kvFmt = "    {:<10s}    =    {}"
        prefix = kvFmt.format('','')

        def wrap(k,v):
            l = kvFmt.format(k,_bibKeyQuote(k,v))
            return textwrap.fill(l,width=100, initial_indent='', subsequent_indent=prefix)

        

        keys = ",\n".join(wrap(*itm) for itm in sorted(btexDict.items(), key=lambda x: self._allFields.index(x[0])))
        return bt.format(type=self.btexType, key=self.key(), keys=keys)

    def _makeCiteKey(self):
        if 'author' in self.meta:
            firstAuth = _unicodeNorm(self.meta['author'][0]['family'].split(' ')[0])
        elif 'editor' in self.meta:
            firstAuth = _unicodeNorm(self.meta['editor'][0]['family'].split(' ')[0])
        else:
            firstAuth = "Unknown"

        firstAuth = re.sub(r'[^a-zA-Z]', '', firstAuth)

        l = sum(1 for x in firstAuth if x.islower())
        u = sum(1 for x in firstAuth if x.isupper())
        n = len(firstAuth)
        if l==n or u==n:
            firstAuth = firstAuth.title()

        year = str(self.meta['issued']['date-parts'][0][0])
        try:
            title = self.meta['title'][-1]
            suffix = list(map(lambda x: x[0].lower(), title.split(' ')))
            suffix = ''.join(suffix[:min(len(suffix),3)])
        except IndexError:
            suffix = 'XXX'
        return firstAuth+year+suffix

    def _metadictpkg(self,k,cr=None):
        if not cr:
            cr = k
        if cr in self.meta:
            return {k:self.meta[cr]}
        return dict()

    def _dict_doi(self):
        return self._metadictpkg('doi', 'DOI')
    
    def _dict_address(self):
        return self._metadictpkg('address', 'publisher-location')

    def _dict_authorOrEditor(self):
        return _mergeDicts(self._dict_author(), self._dict_editor())

    def _dict_author(self):
        v = dict()
        if 'author' in self.meta:
            v['author'] = " and ".join(_parsePerson(a) for a in self.meta['author'])
        return v

    def _dict_editor(self):
        v = dict()
        if 'editor' in self.meta:
            v['editor'] = " and ".join(_parsePerson(a) for a in self.meta['editor'])
        return v

    def _dict_institution(self):
        return self._metadictpkg('institution', 'publisher')

    def _dict_month(self):
        v = dict()
        date = self.meta['issued']['date-parts'][0]
        if len(date) > 1:
            v['month'] = ['', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'][date[1]]
        return v

    def _dict_year(self):
        v = dict()
        date = self.meta['issued']['date-parts'][0]
        if date:
            v['year'] = date[0]
        return v

    def _dict_number(self):
        return self._metadictpkg('number', 'issue')

    def _dict_publisher(self):
        return self._metadictpkg('publisher')

    def _dict_pages(self):
        return self._metadictpkg('pages', 'page')

    def _dict_title(self):
        v = dict()
        if 'title' in self.meta and self.meta['title']:
            v['title'] = self.meta['title'][-1]
        return v

    def _dict_volume(self):
        return self._metadictpkg('volume')

    def _dict_volumeOrNumber(self):
        return _mergeDicts(self._dict_volume(), self._dict_number())


    def format(self, formatter, index=None):
        if index:
            self._index = str(index)
        else:
            self._index = None

        return formatter(self).fmt()

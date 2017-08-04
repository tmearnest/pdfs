from .Logging import log
from .Crossref import crossrefLookup
from .Bibtex import bibtexFields, makeBibtex, makeCiteKey

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

class TypeMapMeta(type):
    def __new__(meta, name, bases, namespace):
        cls = type.__new__(meta, name, bases, namespace)

        if not hasattr(meta, '_typeMap'):
            meta._typeMap = dict()
        else:
            if "_crossrefTypes" not in namespace:
                raise AttributeError("Missing class attribute: _crossrefTypes")
            for x in cls._crossrefTypes:
                meta._typeMap[x] = cls

        return cls

class Entry(metaclass=TypeMapMeta):
    _allFields = bibtexFields
    def __init_subclass__(cls):
        reqClsFields = dict(_reqFields=list, _optFields=list, btexType=str)

        for attr,tp in reqClsFields.items():
            if attr not in dir(cls) or not isinstance(getattr(cls,attr), tp):
                raise AttributeError("Entry subclasses must have a {} attribute called {}".format(tp.__name__, attr))

        for field in cls._allFields:
            dField  = "_dict_" + field

            if not hasattr(cls, dField):
                setattr(cls, dField, lambda s: dict())

            setattr(cls, field, lambda s, field=field: getattr(s, "_dict_"+field)().get(field))

        okFields = cls._optFields + cls._reqFields

        if 'authorOrEditor' in okFields:
            del okFields[okFields.index('authorOrEditor')]
            okFields.append('author')
            okFields.append('editor')

        if 'volumeOrNumber' in okFields:
            del okFields[okFields.index('volumeOrNumber')]
            okFields.append('volume')
            okFields.append('number')

        okFields = set(okFields)

        for field in cls._allFields:
            if field not in okFields:
                setattr(cls, field, lambda s: None)

    def __init__(self, meta, fileLabels=None, citeKey=None, tags=None, files=None, md5s=None, bibtex=None):
        if type(self) is Entry:
            raise RuntimeError("Do not instantiate {} directly".format(type(self).__name__))
        self.meta = meta
        self.tags = tags or list()
        self.files = files or list()
        self.md5s = md5s or list()
        self.fileLabels = fileLabels or list()
        self._citeKey = citeKey or makeCiteKey(meta)
        self.bibtex = bibtex or self.bibtexFromMetadata()

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

        return makeBibtex(self.key(), self.btexType, btexDict)


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

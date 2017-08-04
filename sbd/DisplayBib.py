import re
from .Bibtex import bibtexFields

_nameSepRe = re.compile(r"[., ]+")

def _limitAuthors(btexAuthors):
    people = []
    for person in  btexAuthors.split(" and "):
        names = person.split(',')
        family = names[0]
        given = ','.join(names[1:])
        people.append( family + ' ' + ''.join(x[0].upper() for x in _nameSepRe.split(given) if x))
    if len(people) > 4:
        people = people[:3] + ["…"] + [people[-1]]
    if len(people) < 3:
        s = ' and '.join(people)
    else:
        s =  ', '.join(people[:-1]) + ', and ' + people[-1]
    return s

class FieldDelegate:
    def __init_subclass__(cls):
        for field in bibtexFields + ['key']:
            if not hasattr(cls, field):
                setattr(cls, field, lambda s, field=field: getattr(s.entry,field)() )

class DisplayBib(FieldDelegate):
    def __init__(self, e):
        self.entry = e

    def key_fmt(self):
        s = "[" 
        if self.index():
            s += self.index() + '/'
        s += self.key() + ']'
        return s

    def bib_fmt(self):
        fields = []
        fields.append(self.author())
        fields.append(self.title())

        fs = [self.journal(), self.institution(), self.school(), self.organization(), self.publisher()]
        if self.booktitle():
            t = "In " + self.booktitle()
            if self.series():
                t += ": " + self.series()
            if any(fs):
                t+= ' (' + ', '.join(f for f in fs if f) + ')'
            fields.append(t)
        elif any(fs):
            fields += fs

        fields.append(self.editor())
        fields.append(self.volume())
        fields.append(self.number())
        fields.append(self.pages())
        fields.append("("+self.year() + ")")
        fields.append(self.doi())

        fields = [f for f in fields if f]

        n = len(fields)-1-2

        seps =  ['. '] + [', ']*n + ['. ', '']
        s =  ''.join(''.join(x) for x in zip(fields, seps))

        f = self.tags_fmt()
        if f:
            s += ' '+f
        f = self.attachments_fmt()
        if f:
            s += ' ' + f

        return s


    def tags_fmt(self):
        if self.entry.tags:
            return 'tags: {' + ', '.join(self.tag(t) for t in self.entry.tags) + '}'

    def attachment(self, a):
        return a

    def attachments_fmt(self):
        if len(self.entry.fileLabels)>1:
            return 'attachments: {' + ', '.join(self.attachment(a) for a in self.entry.fileLabels[1:]) + '}'

    def tag(self, t):
        return t


    def fmt(self,index=None):
        if index:
            index = str(index)
        self._index = index
        k = self.key_fmt()
        b = self.bib_fmt()
        return ' '.join(x for x in [k,b] if x)

    def index(self):
        return self._index

    def editor(self):
        e = self.entry.editor()
        if e:
            if len(e.split(" and ")) > 1:
                s = ', eds.'
            else:
                s = ', ed.'

            return _limitAuthors(e) + s

    def pages(self):
        p = self.entry.editor()
        if p:
            if len(p.split("-")) > 1:
                return "pp. " + p
            return "p. " + p

    def author(self):
        a = self.entry.author()
        if a:
            return _limitAuthors(a)

    def volume(self):
        v = self.entry.volume()
        if v:
            return str(v)

    def year(self):
        y = self.entry.year()
        if y:
            return str(self.entry.year())

    def number(self):
        n = self.entry.number()
        if n:
            return str(n)

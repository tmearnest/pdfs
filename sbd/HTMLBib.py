from .BibFormatter import BibFormatter
from .Bibtex import unicodeNorm

def authorNorm(x):
    return unicodeNorm(x).lower().replace(' ', '_')

class HTMLBib(BibFormatter):
    def tag(self, t):
        return '<a class="tags" href="/tag/{0}">{0}</a>'.format(t)

    def tags_fmt(self):
        if self.entry.tags:
            return '<span class="label">Tags: ' + ', '.join(self.tag(t) for t in self.entry.tags) + "</span>"

    def attachment(self, a):
        idx = self.entry.fileLabels.index(a)
        key = self.entry.key()

        ext = self.entry.files[idx].split('.')
        if len(ext)>1:
            ext = ext[-1]
        else:
            ext = 'dat'
         
        fname = "{}-{:04d}.{}".format(key, idx, ext)

        return '<a class="attachment" href="/attachment/{}">{}</a>'.format(fname, a)

    def attachments_fmt(self):
        if len(self.entry.fileLabels) > 1:
            return '<span class="label">Attachments: ' + ', '.join(self.attachment(a) for a in self.entry.fileLabels[1:]) + '</span>'

    def year(self):
        y = super().year()
        return "<b>" + y + "</b>"

    def booktitle(self):
        t = super().booktitle()
        if t:
            return "<i>" + t + "</i>"

    def volume(self):
        v = super().volume()
        if v:
            return "<b>" + v + "</b>"

    def journal(self):
        j = super().journal()
        if j:
            return "<i>" + j + "</i>"

    def doi(self):
        d = super().doi()
        return '<a class="doi" target="_blank" href="https://dx.doi.org/{d}">doi:{d}</a>'.format(d=d)

    def person_fmt(self, s):
        ns = []
        last = ' '.join(s.split()[:-1])
        for i,n in enumerate(s.split(', ')):
            ns.append('<a class="author" href="/author/{}">{}</a>'.format(authorNorm(last), s))
        return ' '.join(ns)

    def fmt(self):
        k = self.key_fmt()
        b = self.bib_fmt()
        t = self.tags_fmt()
        a = self.attachments_fmt()
        if t:
            t += "<br/>"
        else:
            t = ''
        if a:
            a += "<br/>"
        else:
            a = ''

        return ('<dt class="sbd">{key}</dt>\n' +
                '<dd class="sbd">' +
                '{ref}\n' +
                '<br/>\n' +
                '<span class="label">Added: </span><span class="timestamp">{time}</span><br/>' +
                '{tags}'
                '{attachments}'
                '<a class="pdf" target="_blank" href="/{key}.pdf"></a> ' + 
                '<a class="bib" target="_blank" href="/{key}.bib"></a> ' + 
                '<a class="meta" target="_blank" href="/metadata/{key}"></a> ' + 
                '</dd>'
               ).format(ref=super().bib_fmt(), key=super().key(), time=super().timestamp(),tags=t, attachments=a)


def htmlBibliography(works ):
    return '<br/>'.join(HTMLBib(w).fmt() for w in works)

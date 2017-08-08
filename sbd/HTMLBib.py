from .BibFormatter import BibFormatter

class HTMLBib(BibFormatter):
    def tag(self, t):
        return '<span class="tag">{}</span>'.format(t)

    def tags_fmt(self):
        if self.entry.tags:
            return '<br/><span class="label">Tags: ' + ', '.join(self.tag(t) for t in self.entry.tags) + "</span>"

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
            return '<br/><span class="label">Attachments: ' + ', '.join(self.attachment(a) for a in self.entry.fileLabels[1:]) + '</span>'

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

    def key_fmt(self):
        return '<dt class="sbd">' + self.key() + "</dt>"

    def bib_fmt(self):
        return ('<dd class="sbd">{ref}<br/>' +
                '<a class="pdf" target="_blank" href="/{key}.pdf"></a> ' + 
                '<a class="bib" target="_blank" href="/{key}.bib"></a> ' + 
                '<a class="meta" target="_blank" href="/metadata/{key}"></a> ' + 
                '</dd>'
               ).format(ref=super().bib_fmt(), key=super().key())

def htmlBibliography(works ):
    return '<br/>'.join(HTMLBib(w).fmt() for w in works)

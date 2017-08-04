from .DisplayBib import DisplayBib

_template = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>sdb: TITLE-DIR</title>
    <style>
        @import url('https://fonts.googleapis.com/css?family=Crimson+Text:400,400i,700,700i|Lato:300,900');
        div.sbd {
            font-family: 'Crimson Text', serif;
            font-weight: 400;
            margin: 2em auto;
            max-width: 900px;
        }
        dt.sbd {
            font-family: 'Lato', sans-serif;
            font-weight: 300;
        }

        span.label {
            font-family: 'Lato', sans-serif;
            font-weight: 300;
            font-size: 0.8em;
        }

        a {
            text-decoration: none;
            color: black;
        }

        a.doi:hover {
            text-decoration: underline;
        }

        a.attachment {
            text-decoration: none;
            font-style: italic;
            color: #41af00;
        }

        a.doi:attachment {
            text-decoration: underline;
        }

        span.tag {
            font-family: 'Lato', sans-serif;
            color: #a00;
            font-weight: 900;
            padding: 0.1em 0.5em;
        }

        a.meta {
            font-family: 'Lato', sans-serif;
            font-weight: 900;
            font-size: 0.8em;
            color: white;
            padding: 0.1em 0.5em;
            text-decoration: none;
            border-radius: 0.2em;
            background-color: hsl(30, 99%, 38%);
        }

        a.meta::before {
            content: "Meta";
        }


        a.pdf {
            font-family: 'Lato', sans-serif;
            font-weight: 900;
            font-size: 0.8em;
            color: white;
            padding: 0.1em 0.5em;
            text-decoration: none;
            border-radius: 0.2em;
            background-color: hsl(352, 51%, 37%);
        }

        a.pdf::before {
            content: "PDF";
        }

        a.bib {
            font-family: 'Lato', sans-serif;
            font-weight: 900;
            font-size: 0.8em;
            color: white;
            padding: 0.1em 0.5em;
            text-decoration: none;
            border-radius: 0.2em;
            background-color: #3f3f7a;
        }
        a.bib::before {
            content: "BIB";
        }
    </style>
  </head>
  <body>
    <div class="sbd">
       <h1>Articles under “TITLE-DIR”</h1>
       <dl>
           BIB-BODY
       </dl>
    </div>
  </body>
</html>
"""

class HTMLBib(DisplayBib):
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
        return '<a class="doi" href="https://dx.doi.org/{d}">doi:{d}</a>'.format(d=d)

    def key_fmt(self):
        return '<dt class="sbd">' + self.key() + "</dt>"

    def bib_fmt(self):
        return ('<dd class="sbd">{ref}<br/>' +
                '<a class="pdf" href="/{key}.pdf"></a> ' + 
                '<a class="bib" href="/{key}.bib"></a> ' + 
                '<a class="meta" href="/metadata/{key}"></a> ' + 
                '</dd>'
               ).format(ref=super().bib_fmt(), key=super().key())


def htmlBibliography(works, directory):
    return _template.replace('BIB-BODY', '<br/>'.join(w.format(HTMLBib) for w in works)).replace('TITLE-DIR', directory)

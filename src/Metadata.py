import subprocess, re, logging, functools
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

log = logging.getLogger(__name__)

from html.parser import HTMLParser
import html.entities

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.result = [ ]

    def handle_data(self, d):
        self.result.append(d)

    def handle_charref(self, number):
        codepoint = int(number[1:], 16) if number[0] in (u'x', u'X') else int(number)
        self.result.append(unichr(codepoint))

    def handle_entityref(self, name):
        codepoint = html.entities.name2codepoint[name]
        self.result.append(unichr(codepoint))

    def get_text(self):
        return u''.join(self.result)

def sanitizeHtml(html):
    html = ' '.join(html.split())
    s = HTMLTextExtractor()
    s.feed(html)
    return s.get_text()

class Article:
    def __setattr__(self,attr,obj):
        try:
            log.debug("Article: {} → {}".format(attr,obj))
        except:
            log.debug("Article: set {}".format(attr))
        self.__dict__[attr] = obj

    def line(s):
        if len(s.authors) == 1:
            author = s.authors[0][1]
        elif len(s.authors) == 2:
            author = s.authors[0][1] + " and " + s.authors[-1][1]
        else:
            author = s.authors[0][1] + ", ..., " + s.authors[-1][1]

        return "[{}] {}, \"{}\", {}.".format(s.key,author, s.title, s.abbrJournalName)


@functools.lru_cache()
def getPdfText(fname):
    return subprocess.check_output(['pdftotext', fname, '-']).decode('utf-8')


def guessDoi(fname):
    txt = getPdfText(fname)
    m = re.search(r'(10\.\d{4}[\d\:\.\-\/a-zA-Z]+)',txt)
    if m:
        dois  = set(m.groups())
        doi = m.group(1)
        if len(dois)>1:
            log.warn("Multiple dois found: {}".format(", ".join(dois)))
        return doi
    else:
        return None

def getMetaData(doi):
    url = 'http://www.crossref.org/openurl/?'
    url += urlencode({ "id" : "doi:" + doi, "noredirect" : "true","pid" : 'tmearnest@gmail.com', "format" : "unixref" })
    etree = ET.parse(urlopen(url))
    xml = etree.getroot()
    etree.write("last.xml")

    article = Article()
    jd = xml.find('doi_record/crossref/journal')

    def maybeGetStrip(path_,xml=jd):
        if path_.__class__ == str:
            path = path_
            try:
                 elem = xml.find(path)
            except AttributeError:
                 return None
        else:
            for path in path_:
                try:
                    elem = xml.find(path)
                    break
                except AttributeError:
                    pass
            else:
                return None

        return sanitizeHtml(ET.tostring(elem).decode("UTF-8"))

    def maybeGet(path_,elem=jd):
        if path_.__class__ == str:
            path = path_
            try:
                 val = elem.find(path).text
            except AttributeError:
                 val = None
        else:
            for path in path_:
                try:
                    val = elem.find(path).text
                except AttributeError:
                    pass
            else:
                val = None
        return val

    article.abbrJournalName = maybeGet('journal_metadata/abbrev_title')
    article.journalName = maybeGet('journal_metadata/full_title')
    if article.abbrJournalName is None:
        article.abbrJournalName = article.journalName
    article.title = maybeGetStrip("journal_article/titles/title")

    article.authors = []
    for c in jd.find("journal_article/contributors"):
        article.authors.append( (maybeGet('given_name',c), maybeGet('surname',c)) )

    try:
        pubData = filter(lambda x:x.get('media_type')=='online', jd.findall("journal_article/publication_date")).__next__()
        article.pubMonth = maybeGet('month',pubData)
        article.pubYear = maybeGet('year',pubData)
        article.pubDay = maybeGet('day',pubData)
    except StopIteration:
        article.pubMonth = maybeGet('journal_issue/publication_date/month')
        article.pubYear = maybeGet('journal_issue/publication_date/year')
        article.pubDay = maybeGet('journal_issue/publication_date/day')
    article.issueNumber = maybeGet('journal_issue/issue')
    article.volumeNumber = maybeGet('journal_issue/journal_volume/volume')

    article.pages = (maybeGet(['journal_article/pages/first_page', 'journal_article/publisher_item/item_number']),
                     maybeGet('journal_article/pages/last_page'))

    article.doi = doi

    return article
    

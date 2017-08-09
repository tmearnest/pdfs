import re
import unicodedata
import textwrap
from .unimap import separator_map, char_map

bibtexTypes = ["article", "book", "booklet", "conference", "inbook", "incollection",
              "inproceedings", "manual", "mastersthesis", "misc", "phdthesis",
              "proceedings", "techreport", "unpublished"]


bibtexFields = ["author", "title", "booktitle", "series", "journal", "edition", 
              "editor", "institution", "organization", "publisher", "school", 
              "address", "chapter", "volume", "number", "pages", "year", 
              "month", "doi"]


_regularizeWsRe = re.compile(r"\s+")
def _regularizeWs(x):
    return _regularizeWsRe.sub(' ', x)

def unicodeNorm(x):
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

def makeBibtex(key, btexType, btexDict):
    bt = "@{type}{{{key},\n{keys}\n}}\n"
    kvFmt = "    {:<10s}    =    {}"
    prefix = kvFmt.format('','')

    def wrap(k,v):
        l = kvFmt.format(k,_bibKeyQuote(k,v))
        return textwrap.fill(l,width=100, initial_indent='', subsequent_indent=prefix)

    keys = ",\n".join(wrap(*itm) for itm in sorted(btexDict.items(), key=lambda x: bibtexFields.index(x[0])))
    return bt.format(type=btexType, key=key, keys=keys)

def makeCiteKey(meta):
    if 'author' in meta:
        firstAuth = unicodeNorm(meta['author'][0]['family'].split(' ')[0])
    elif 'editor' in meta:
        firstAuth = unicodeNorm(meta['editor'][0]['family'].split(' ')[0])
    else:
        firstAuth = "Unknown"

    firstAuth = re.sub(r'[^a-zA-Z]', '', firstAuth)

    l = sum(1 for x in firstAuth if x.islower())
    u = sum(1 for x in firstAuth if x.isupper())
    n = len(firstAuth)
    if l==n or u==n:
        firstAuth = firstAuth.title()

    year = str(meta['issued']['date-parts'][0][0])
    try:
        title = meta['title'][-1]
        suffix = list(map(lambda x: x[0].lower(), title.split(' ')))
        suffix = ''.join(suffix[:min(len(suffix),3)])
    except IndexError:
        suffix = 'XXX'
    return firstAuth+year+suffix

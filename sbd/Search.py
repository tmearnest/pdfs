import whoosh.index as widx
import whoosh.qparser as wqp
import whoosh.fields as wfield
import whoosh.query as wq
import whoosh.highlight as highlight
import termcolor as tc
import textwrap




class ANSIFormatter(highlight.Formatter):
    def format_token(self, text, token, replace=False):
        tokentext = highlight.get_text(text, token, replace)
        return tc.colored(tokentext, 'cyan', attrs=['bold'])

    def format(self, fragments, replace=False):
        return textwrap.fill(super().format(fragments, replace), width=80, initial_indent="   ", subsequent_indent="   ")



def _formatterFactory(fmt):
    if fmt.lower() == 'ansi':
        return ANSIFormatter()
    elif fmt.lower() == 'html':
        return highlight.HtmlFormatter()
    else:
        raise NotImplementedError


class Search:
    @staticmethod
    def initialize(indexDir):
        schema = wfield.Schema(kind=wfield.ID,
                               key=wfield.ID(stored=True, unique=True), 
                               srcKey=wfield.ID(stored=True),
                               page=wfield.NUMERIC(stored=True, sortable=True), 
                               text=wfield.TEXT(stored=True),
                               md5=wfield.ID,
                               bibtex=wfield.TEXT(stored=True),
                               title=wfield.TEXT(stored=True),
                               authors=wfield.TEXT(stored=True),
                               year=wfield.NUMERIC(stored=True, sortable=True), 
                               pub=wfield.TEXT(stored=True), 
                               doi=wfield.ID(stored=True))
        widx.create_in(indexDir, schema)

    def __init__(self,indexDir):
        self.ix = widx.open_dir(indexDir)

    def keyExists(self, key):
        with self.ix.searcher() as searcher:
            query = wqp.QueryParser("key", self.ix.schema).parse(key)
            results = searcher.search(query)
            return len(results) > 0

    def getBibTex(self, key=None):
        with self.ix.searcher() as searcher:
            if key is None:
                query = wq.Every("key")
            else:
                query = wqp.QueryParser("key", self.ix.schema).parse(key)
            bt = []
            for r in searcher.search(query, limit=None):
                bt.append(r['bibtex'])
            return bt


    def findByMd5(self, md5):
        with self.ix.searcher() as searcher:
            query = wqp.QueryParser("md5", self.ix.schema).parse(md5)
            results = searcher.search(query)
            for hit in results:
                return hit['key']
            else:
                return None

    def listAll(self):
        with self.ix.searcher() as searcher:
            results = []
            for hit in  searcher.documents(kind='bib'):
                results.append(dict(
                    key=hit['key'],
                    authors=hit['authors'],
                    title=hit['title'],
                    year=hit['year'],
                    pub=hit['pub'],
                    doi=hit['doi']))

        return results

    def searchKey(self, key, term, formatter="ansi"):
        with self.ix.searcher() as searcher:
            q = wq.Term("kind", "bib") & wqp.QueryParser(key, self.ix.schema).parse(term)
            results = searcher.search(q, limit=None)
            results.fragmenter = highlight.WholeFragmenter()
            results.formatter = _formatterFactory(formatter)
            rs = []
            for hit in results:
                r = dict(score=hit.score)
                for k in ['key', 'bibtex', 'authors', 'title', 'year', 'pub', 'doi']:
                    if key == k:
                        r[k] = ' '.join(hit.highlights(k).split())
                    else:
                        r[k] = hit[k]
                rs.append(r)
            return sorted(rs, key=lambda x: -x['score'])

    def search(self, term, formatter='ansi'):
        with self.ix.searcher() as searcher:
            q = wq.Term("kind", "page") & wqp.QueryParser("text", self.ix.schema).parse(term)
            pgResults = searcher.search(q, limit=None)
            pgResults.fragmenter.charlimit = None
            pgResults.formatter = _formatterFactory(formatter)
            pgDict = {}

            for hit in pgResults:
                sk = hit['srcKey']
                if sk in pgDict:
                    pgDict[sk].append(hit)
                else:
                    pgDict[sk]=[hit]

            rs = []

            for k,pgs in pgDict.items():
                bibhit = searcher.document(key=k)

                pgData = sorted([[h['page'], h.score, h.highlights("text")] for h in pgs])
                totalScore = sum(x[1] for x in pgData)

                r = dict(key=bibhit['key'],
                         bibtex=bibhit['bibtex'],
                         authors=bibhit['authors'],
                         title=bibhit['title'],
                         year=bibhit['year'],
                         pub=bibhit['pub'],
                         pages=[x[0] for x in pgData],
                         text=[x[2] for x in pgData],
                         pageScores=[x[1] for x in pgData],
                         doi=bibhit['doi'],
                         score=totalScore)
                rs.append(r)
            return sorted(rs, key=lambda x: -x['score'])

   
    def addFulltext(self, b, pages):
        with self.ix.writer() as writer:
            writer.add_document(kind='bib',
                                key=b['key'],
                                md5=b['md5'],
                                bibtex=b['bib'],
                                authors=b['authors'],
                                title=b['title'],
                                year=b['year'],
                                pub=b['pub'],
                                doi=b['doi'])
            for i,text in enumerate(pages):
                writer.add_document(kind='page',
                                    srcKey=b['key'],
                                    page=i,
                                    text=text)

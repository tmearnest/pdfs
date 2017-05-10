import whoosh.index as widx
import whoosh.qparser as wqp
import whoosh.query as wq
import whoosh.fields as wfield
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


class TextSearch:
    @staticmethod
    def initialize(indexDir):
        schema = wfield.Schema(key=wfield.ID(stored=True),
                               kind=wfield.TEXT(stored=True),
                               page=wfield.NUMERIC(stored=True, sortable=True), 
                               text=wfield.TEXT(stored=True))
        widx.create_in(indexDir, schema)

    def __init__(self,indexDir):
        self.ix = widx.open_dir(indexDir)

    def searchNote(self, term, formatter='ansi'):
        with self.ix.searcher() as searcher:
            q = wq.Term("kind", "note") & wqp.QueryParser("text", self.ix.schema).parse(term)
            results = searcher.search(q, limit=None)
            results.fragmenter=highlight.WholeFragmenter()
            results.formatter = _formatterFactory(formatter)
            pgDict = {}

            for hit in results:
                sk = hit['key']
                pgDict[sk] = dict(text=hit.highlights("text"), score=hit.score)

            return sorted(pgDict.items(), key=lambda x: -x[1]['score'])



    def search(self, term, formatter='ansi'):
        with self.ix.searcher() as searcher:
            q = wq.Term("kind", "page") & wqp.QueryParser("text", self.ix.schema).parse(term)
            results = searcher.search(q, limit=None)
            results.fragmenter.charlimit = None
            results.formatter = _formatterFactory(formatter)
            pgDict = {}

            for hit in results:
                sk = hit['key']
                r = dict(page=hit['page'], text=hit.highlights("text"), score=hit.score)

                if sk in pgDict:
                    pgDict[sk].append(r)
                else:
                    pgDict[sk] = [r]

            return sorted(pgDict.items(), key=lambda x: -sum(y['score'] for y in x[1]))


    def getNote(self, key):
        with self.ix.searcher() as searcher:
            q = wq.Term("kind", "note") & wq.Term("key", key)
            results = searcher.search(q, limit=None)
            for hit in results:
                return hit['text']

    def delNote(self, key):
        with self.ix.writer() as writer:
            q = wq.Term("kind", "note") & wq.Term("key", key)
            writer.delete_by_query(q)

    def addNote(self, key, text):
        self.delNote(key)
        with self.ix.writer() as writer:
            writer.add_document(key=key,
                                kind='note',
                                text=text)
   
    def addFulltext(self, key, pages):
        with self.ix.writer() as writer:
            for i,text in enumerate(pages):
                writer.add_document(key=key,
                                    kind='page',
                                    page=i,
                                    text=text)


    def renameKey(self, old, new):
        docs = []
        q = wq.Term("key", old)
        with self.ix.searcher() as searcher:
            results = searcher.search(q, limit=None)
            for hit in results:
                k = hit['kind']
                if k == 'page':
                    docs.append(
                            dict(key=new,
                                 kind="page",
                                 page=hit['page'],
                                 text=hit['text']))
                elif k == 'note':
                    docs.append(
                            dict(key=new,
                                 kind="note",
                                 text=hit['text']))
                else:
                    raise ValueError("unknown document type: {}".format(k))

        with self.ix.writer() as writer:
            writer.delete_by_query(q)

        with self.ix.writer() as writer:
            for d in docs:
                if d['kind'] == 'page':
                    writer.add_document(key=d['key'],
                                        kind=d['kind'],
                                        page=d['page'],
                                        text=d['text'])
                elif d['kind'] == 'note':
                    writer.add_document(key=d['key'],
                                        kind=d['kind'],
                                        text=d['text'])
                else:
                    raise ValueError

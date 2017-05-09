import whoosh.index as widx
import whoosh.qparser as wqp
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


class Search:
    @staticmethod
    def initialize(indexDir):
        schema = wfield.Schema(key=wfield.ID(stored=True),
                               page=wfield.NUMERIC(stored=True, sortable=True), 
                               text=wfield.TEXT(stored=True))
        widx.create_in(indexDir, schema)

    def __init__(self,indexDir):
        self.ix = widx.open_dir(indexDir)

    def search(self, term, formatter='ansi'):
        with self.ix.searcher() as searcher:
            q = wqp.QueryParser("text", self.ix.schema).parse(term)
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
   
    def addFulltext(self, key, pages):
        with self.ix.writer() as writer:
            for i,text in enumerate(pages):
                writer.add_document(key=key,
                                    page=i,
                                    text=text)

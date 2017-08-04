from .Entry import Entry

class TechReport(Entry):
    btexType="techreport"
    _crossrefTypes = ['report']
    _reqFields=["doi", "author", "title", "institution", "year"]
    _optFields=["number", "address", "month"]

class Dissertation(Entry):
    _crossrefTypes = ['dissertation']
    _reqFields = ["doi", "author", "title", "school", "year"]
    _optFields = ["address", "month"]
    btexType = "phdthesis"

    def _dict_school(self):
        v = dict()
        if 'publisher' in self.meta:
            v['school'] = self.meta['publisher']
        return v

class JournalArticle(Entry):
    _crossrefTypes = ['journal-article', "reference-entry", "posted-content"]
    _reqFields=["doi", "author", "title", "journal", "year", "volume"]
    _optFields=["number", "pages", "month"]
    btexType="article"

    def _dict_journal(self):
        v = dict()
        if 'container-title' in self.meta:
            v['journal']  = self.meta['container-title'][0]
        return v

class ProceedingsArticle(Entry):
    _crossrefTypes = ["proceedings-article"]
    _reqFields=["doi", "author", "title", "booktitle", "year"]
    _optFields=["editor", "volumeOrNumber", "series", "pages", "address", "month", "organization", "publisher"]
    btexType = "inproceedings"

    def _dict_address(self):
        v = dict()
        if 'event' in self.meta and 'location' in self.meta['event']:
            v['address'] = self.meta['event']['location']
            return v
        return super().address()

    def _dict_booktitle(self):
        v = dict()
        if 'event' in self.meta and 'name' in self.meta['event']:
            v['booktitle'] = self.meta['event']['name']
        return v

class BookChapter(Entry):
    _crossrefTypes = ["book-chapter"]
    _reqFields=["doi", "author", "title", "booktitle", "publisher", "year"]
    _optFields=["editor", "volumeOrNumber", "series", "chapter", "pages", "address", "edition", "month"]
    btexType="incollection"

    def _dict_booktitle(self):
        v = dict()
        v['booktitle'] = self.meta['container-title'][-1]
        return v

    def _dict_series(self):
        v = dict()
        if len(self.meta['container-title']) > 1:
            v['series'] = self.meta['container-title'][0]
        return v

class Book(Entry):
    _reqFields=["doi", "authorOrEditor", "title", "publisher", "year"]
    _optFields=["volumeOrNumber", "series", "address", "edition", "month"]
    _crossrefTypes = ["book", "reference-book"]
    btexType="book"

    def _dict_booktitle(self):
        v = dict()
        v['booktitle'] = self.meta['title'][-1]
        return v

    def _dict_series(self):
        v = dict()
        if len(self.meta['title']) > 1:
            v['series'] = self.meta['title'][0]
        return v

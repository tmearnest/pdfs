import whoosh.index as widx
import whoosh.qparser as wqp
from whoosh.fields import *

class Search:

   @staticmethod
   def initialize(indexDir):
      schema = Schema(key=TEXT(stored=True), text=TEXT)
      widx.create_in(indexDir, schema)

   def __init__(self,indexDir):
      self.ix = widx.open_dir(indexDir)

   def search(self, term):
      with self.ix.searcher() as searcher:
          query = wqp.QueryParser("text", self.ix.schema).parse(term)
          results = searcher.search(query)
          return [x['key'] for x in results]
   
   def addDocument(self, key, text):
      with self.ix.writer() as writer:
         writer.add_document(key=key,text=text)
         # writer.commit()


import sqlite3, unidecode, logging, os
from .Metadata import Article

log = logging.getLogger(__name__)

class BibDB:
    def __init__(self,dbFile):
        conn = self.conn = sqlite3.connect(dbFile)


    @staticmethod
    def initialize(dbFile):
        try:
            os.unlink(dbFile)
        except FileNotFoundError:
            pass

        conn = sqlite3.connect(dbFile)
        cur = conn.cursor()
        cur.execute("""CREATE TABLE bib(id INTEGER PRIMARY KEY, 
                                        key TEXT COLLATE NOCASE,
                                        journalId INTEGER, 
                                        title TEXT COLLATE NOCASE,
                                        pubDay TEXT,
                                        pubMonth TEXT,
                                        pubYear TEXT,
                                        issueNumber TEXT,
                                        volumeNumber TEXT,
                                        pagesStart TEXT,
                                        pagesEnd TEXT,
                                        doi TEXT)""")
        cur.execute("""CREATE TABLE authors(id INTEGER PRIMARY KEY,
                                            firstName TEXT COLLATE NOCASE, 
                                            lastName TEXT COLLATE NOCASE)""")
        cur.execute("""CREATE TABLE bibAuthors(id INTEGER PRIMARY KEY,
                                               bibId INTEGER, 
                                               authorId INTEGER)""")
        cur.execute("""CREATE TABLE journals(id INTEGER PRIMARY KEY,
                                             name TEXT COLLATE NOCASE, 
                                             abbrName TEXT COLLATE NOCASE)""")
        cur.execute("""CREATE TABLE tags(id INTEGER PRIMARY KEY,
                                         tag TEXT COLLATE NOCASE)""")
        cur.execute("""CREATE TABLE bibTags(id INTEGER PRIMARY KEY,
                                            bibId INTEGER,
                                            tagId INTEGER)""")


    def insertArticle(self, article):
       done,ct = False, 0
       firstAuthor = ''.join(unidecode.unidecode(a).capitalize() for a in article.authors[0][1].split())
       year = str(article.pubYear)
       tag = ''.join(x[0].lower() for x in article.title.split())[:3]
       baseKey = firstAuthor+year+tag

       cur = self.conn.cursor()

       while not done:
           if ct-1 >= 0:
               suffix = str(ct-1)
           else:
               suffix = ''
           key = baseKey+suffix

           cur.execute("SELECT doi FROM bib WHERE key=?",(key,))
           row = cur.fetchone()
           if row is None:
               done = True
           else:
               if article.doi == row[0]:
                   log.error("doi:{} exists in the database".format(article.doi))
                   exit(1)

       article.key = key
       
       authorIds = []
       for first,last in article.authors:
           cur.execute("SELECT * FROM authors WHERE firstName=? and lastName=?",(first,last) )

           row = cur.fetchone()
           if row is None:
               cur.execute("INSERT INTO authors(firstName,lastName) VALUES(?,?)", (first,last))
               authorIds.append(cur.lastrowid)
           else:
               authorIds.append(row[0])

       tagIds = []
       for tag in article.tags:
           cur.execute("SELECT id FROM tags WHERE tag=?",(tag,) )
           row = cur.fetchone()
           if row is None:
               cur.execute("INSERT INTO tags(tag) VALUES(?)", (tag,))
               tagIds.append(cur.lastrowid)
           else:
               tagIds.append(row[0])


       cur.execute("SELECT * FROM journals WHERE name=?", (article.journalName,))
       row = cur.fetchone()
       if row is None:
           cur.execute("INSERT INTO journals(name, abbrName) VALUES(?,?)", (article.journalName,article.abbrJournalName))
           journalId = cur.lastrowid
       else:
           journalId = row[0]


       cur.execute("""INSERT INTO bib(key, journalId, title, pubDay, 
                                      pubMonth, pubYear, issueNumber, volumeNumber, 
                                      pagesStart, pagesEnd, doi)
                                  VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (key, journalId, article.title, article.pubDay, article.pubMonth, 
                    article.pubYear, article.issueNumber, article.volumeNumber, article.pages[0],
                    article.pages[1], article.doi) )

       bibId = cur.lastrowid

       cur.executemany("""INSERT INTO bibAuthors(bibId, authorId) VALUES(?, ?)""", [(bibId,a) for a in authorIds])
       cur.executemany("""INSERT INTO bibTags(bibId, tagId) VALUES(?, ?)""", [(bibId,a) for a in tagIds])
       self.conn.commit()


    def getArticles(self, key=None, author=None, year=None, journal=None,doi=None,tag=None):
      if sum(x is not None for x in [tag,key,author,year,journal,doi] ) != 1:
          raise RuntimeError("must specify only one search term")

      cur = self.conn.cursor()

      if key is not None:
          return [ self.getArticleByKey(key) ]
      elif author is not None:
          cur.execute("""SELECT bib.key 
                         FROM bib
                         JOIN bibAuthors ON bibAuthors.bibId==bib.id 
                         JOIN authors ON authors.id == bibAuthors.authorId
                         WHERE authors.firstName=? OR authors.lastName=?""", (author,author,))
          return [ self.getArticleByKey(k) for k, in cur.fetchall() ]
      elif year is not None:
          cur.execute("""SELECT bib.key 
                         FROM bib
                         WHERE bib.year=?""", (year,))
          return [ self.getArticleByKey(k) for k, in cur.fetchall() ]
      elif journal is not None:
          cur.execute("""SELECT bib.key 
                         FROM bib
                         JOIN journals ON bib.journalId=journals.id 
                         WHERE journals.name=? OR journals.abbrName=?""", (journal,journal))
          return [ self.getArticleByKey(k) for k, in cur.fetchall() ]
      elif doi is not None:
          cur.execute("""SELECT bib.key 
                         FROM bib
                         WHERE bib.doi=?""", (doi,))
          return [ self.getArticleByKey(k) for k, in cur.fetchall() ]
      elif tag is not None:
          cur.execute("""SELECT bib.key 
                         FROM bib
                         JOIN bibTags ON bibTags.bibId==bib.id 
                         JOIN tags ON tags.id == bibTags.tagId
                         WHERE tags.tag=?""", (tag,))
          return [ self.getArticleByKey(k) for k, in cur.fetchall() ]
      else:
         return []
          

    def getArticleByKey(self,key):
      article = Article()
      cur = self.conn.cursor()
      cur.execute("""SELECT bib.doi,
                            journals.name,
                            journals.abbrName,
                            bib.title,
                            bib.pubDay,
                            bib.pubMonth,
                            bib.pubYear,
                            bib.issueNumber,
                            bib.volumeNumber,
                            bib.pagesStart,
                            bib.pagesEnd,
                            bib.id
                     FROM bib 
                     JOIN journals ON bib.journalId=journals.id 
                     WHERE bib.key=?""", (key,))

      row = cur.fetchone()

      article.key=key
      article.doi,            \
      article.journalName,    \
      article.abbrJournalName,\
      article.title,          \
      article.pubDay,         \
      article.pubMonth,       \
      article.pubYear,        \
      article.issueNumber,    \
      article.volumeNumber = row[:-3]
      article.pages=(row[-3],row[-2])
      bibId = row[-1]

      cur.execute("""SELECT authors.firstName, authors.lastName
                     FROM authors
                     JOIN bibAuthors ON bibAuthors.authorId=authors.id
                     WHERE bibAuthors.bibId=?""", (bibId,))
      rows = cur.fetchall()

      article.authors = [(r[0], r[1]) for r in rows]
      
      cur.execute("""SELECT tags.tag
                     FROM tags
                     JOIN bibTags ON bibTags.tagId=tags.id
                     WHERE bibTags.bibId=?""", (bibId,))
      rows = cur.fetchall()
      article.tags = [r[0] for r in rows]

      return article
    


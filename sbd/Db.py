import contextlib
import datetime
import os
import sqlite3

from pybtex.database import BibliographyData, Entry, Person
from .Logging import log

@contextlib.contextmanager
def SqlCursor(dbFile):
    conn = sqlite3.connect(dbFile)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    yield cur
    conn.commit()
    conn.close()


class DB:
    def __init__(self,dbFile):
        self.dbFile = dbFile

    @staticmethod
    def initialize(dbFile):
        try:
            os.unlink(dbFile)
        except FileNotFoundError:
            pass

        with SqlCursor(dbFile) as cur:
            cur.execute("""
                CREATE TABLE bib(id INTEGER PRIMARY KEY,
                                 citeKey TEXT COLLATE NOCASE,
                                 pmid TEXT,
                                 pdfMd5 TEXT,
                                 addDate TEXT,
                                 entryType TEXT,
                                 bk_doi TEXT,
                                 bk_address TEXT,
                                 bk_annote TEXT,
                                 bk_booktitle TEXT,
                                 bk_chapter TEXT,
                                 bk_crossref TEXT,
                                 bk_edition TEXT,
                                 bk_howpublished TEXT,
                                 bk_institution TEXT,
                                 bk_journal TEXT,
                                 bk_key TEXT,
                                 bk_month TEXT,
                                 bk_note TEXT,
                                 bk_number TEXT,
                                 bk_organization TEXT,
                                 bk_pages TEXT,
                                 bk_publisher TEXT,
                                 bk_school TEXT,
                                 bk_series TEXT,
                                 bk_title TEXT,
                                 bk_type TEXT,
                                 bk_volume TEXT,
                                 bk_year TEXT)
            """)
            cur.execute("""
                CREATE TABLE people(id INTEGER PRIMARY KEY,
                                    first TEXT COLATE NOCASE, 
                                    middle TEXT COLATE NOCASE, 
                                    last TEXT COLATE NOCASE)
            """)
            cur.execute("""
                CREATE TABLE authors(id INTEGER PRIMARY KEY,
                                     bibId  INTEGER,
                                     personId INTEGER)
            """)
            cur.execute("""
                CREATE TABLE editors(id INTEGER PRIMARY KEY,
                                     bibId  INTEGER,
                                     personId INTEGER)
            """)
            cur.execute("""
                CREATE TABLE bibTags(id INTEGER PRIMARY KEY,
                                     bibId INTEGER,
                                     tagId INTEGER)
            """)
            cur.execute("""
                CREATE TABLE tags(id INTEGER PRIMARY KEY,
                                  tag TEXT)
            """)


    @staticmethod
    def _unwrapFirst(rs):
        return [x[0] for x in rs]


    @staticmethod
    def _lookupPerson(cur, first,  middle, last):
        cur.execute("SELECT * FROM people WHERE first=? and middle=? and last=?",(first,middle,last) )
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO people(first,middle,last) VALUES(?,?,?)", (first,middle,last))
            return cur.lastrowid
        return row[0]


    @staticmethod
    def _findTag(cur,tag):
        cur.execute("SELECT * FROM tags WHERE tag=?",(tag,))
        row = cur.fetchone()
        if row is None:
            return None
        return row[0]


    @classmethod
    def _lookupTag(cls,cur, tag):
        tag = tag.lower()
        tid = cls._findTag(cur,tag)
        if tid is None:
            cur.execute("INSERT INTO tags(tag) VALUES(?)", (tag,))
            return cur.lastrowid
        return tid


    @classmethod
    def _lookupBibIdPerson(cls, cur, key, value):
        sql = """
            SELECT bib.id
            FROM bib
            JOIN {key} 
                ON {key}.bibId==bib.id
            JOIN people 
                ON people.id=={key}.personId
            WHERE 
                people.first like "%{value}%" 
                OR 
                people.middle like "%{value}%" 
                OR 
                people.last like "%{value}%"
        """.format(key=key, value=value)
        cur.execute(sql)
        return cls._unwrapFirst(cur.fetchall())


    @classmethod
    def _bibIdFromCiteKey(cls, cur, value):
        cur.execute("SELECT bib.id FROM bib WHERE bib.citeKey==?", (value,))
        return cls._unwrapFirst(cur.fetchall())


    @classmethod
    def _lookupBibId(cls, cur, key, value):
        if key=='authors':
            return cls._lookupBibIdPerson(cur, 'authors', value)
        elif key=='editors':
            return cls._lookupBibIdPerson(cur, 'editors', value)
        elif key=='tag':
            cur.execute("""
                SELECT bib.id
                FROM bib
                JOIN bibTags 
                    ON bibTags.bibId==bib.id
                JOIN tags 
                    ON tags.id==bibTags.tagId
                WHERE tags.tag=?
            """, (value,))
            return cls._unwrapFirst(cur.fetchall())

        cur.execute('SELECT bib.id FROM bib WHERE bib.{key} LIKE "%{value}%"'.format(key=key,value=value))
        return cls._unwrapFirst(cur.fetchall())


    @staticmethod
    def _dictsToBib(ds):
        db = BibliographyData()
        empty = True
        for d in ds:
            empty = False
            bib = Entry(d['entryType'])
            if d['authors']:
                bib.persons['author'] = [Person(" ".join(ns)) for ns in d['authors']]
            if d['editors']:
                bib.persons['editor'] = [Person(" ".join(ns)) for ns in d['editors']]

            for k,v in d.items():
                if k.startswith("bk_"):
                    if v is not None:
                        bib.fields[k[3:]] = v
            db.add_entry(d['citeKey'], bib)
        return None if empty else db
            

    @staticmethod
    def _bibDataById(cur, bibId):
        cur.execute("SELECT * from bib WHERE bib.id=?", (bibId,))
        result = None
        for row in cur:
            result = dict(row)

        cur.execute("""
            SELECT tags.tag
            FROM bibTags
            JOIN tags ON tags.id==bibTags.tagId
            WHERE bibTags.bibId==?
        """, (bibId,))

        cur.execute("""
            SELECT people.first, people.middle, people.last
            FROM authors
            JOIN people ON people.id==authors.personId
            WHERE authors.bibId==?
        """, (bibId,))

        result['authors'] = []
        for row in cur:
            result['authors'].append((row[0],row[1],row[2]))

        cur.execute("""
            SELECT people.first, people.middle, people.last
            FROM editors
            JOIN people ON people.id==editors.personId
            WHERE editors.bibId==?
        """, (bibId,))

        result['editors'] = []
        for row in cur:
            result['editors'].append((row[0],row[1],row[2]))

        return result


    def modTags(self, citeKey, tagDiff):
        addTags = [x[1:] if x[0] == '+' else x for x in tagDiff if x[0] != '-']
        delTags = [x[1:] for x in tagDiff if x[0] == '-']
        
        with SqlCursor(self.dbFile) as cur:
            bibId = self._bibIdFromCiteKey(cur,citeKey)[0]
            for tag in delTags:
                tid = self._findTag(cur, tag)
                if tid is None:
                    log.warning("Tag %s not found", tag)
                else:
                    cur.execute("DELETE from bibTags WHERE tagId=? AND bibId=?", (tid,bibId))
                    cur.execute("SELECT bibId from bibTags WHERE tagId=?", (tid,))
                    row = cur.fetchone()
                    if row is None:
                        cur.execute("DELETE from tags WHERE id=?", (tid,))
            for tag in addTags:
                tid = self._lookupTag(cur,tag)
                cur.execute("SELECT * from bibTags WHERE tagId=? AND bibId=?", (tid,bibId))
                row = cur.fetchone()
                if row is None:
                    cur.execute("INSERT INTO bibTags(bibId, tagId) VALUES(?, ?)", (bibId, tid))


    def delBibtex(self, searchCiteKey):
        with SqlCursor(self.dbFile) as cur:
            for bibId in self._bibIdFromCiteKey(cur, searchCiteKey):
                def tagset(table, field, selField, val):
                    cur.execute("SELECT {field} FROM {table} "
                                "WHERE {selField}=?".format(table=table,field=field,selField=selField), (val,))
                    return set(self._unwrapFirst(cur.fetchall()))

                oldPeople = (tagset("authors", "personId", "bibId", bibId)
                              | tagset("editors", "personId", "bibId", bibId))
                oldTags = tagset("bibTags", "tagId", "bibId", bibId)
                
                cur.execute("DELETE FROM bib WHERE id=?", (bibId,))
                cur.execute("DELETE FROM authors WHERE bibId=?", (bibId,))
                cur.execute("DELETE FROM editors WHERE bibId=?", (bibId,))
                cur.execute("DELETE FROM bibTags WHERE bibId=?", (bibId,))
                
                for pid in oldPeople:
                    cur.execute("SELECT * FROM authors WHERE personId=?", (pid, ))
                    personExists = cur.fetchone() is not None
                    cur.execute("SELECT * FROM editors WHERE personId=?", (pid, ))
                    personExists = personExists or (cur.fetchone() is not None)
                    if not personExists:
                        cur.execute("DELETE FROM people WHERE id=?", (pid,))

                for tid in oldTags:
                    cur.execute("SELECT * FROM bibTags WHERE tagId=?", (tid, ))
                    tagExists = cur.fetchone() is not None
                    if not tagExists:
                        cur.execute("DELETE FROM tags WHERE id=?", (tid, ))


    def getTags(self, citeKey):
        with SqlCursor(self.dbFile) as cur:
            cur.execute("""
                SELECT tag 
                FROM bib 
                JOIN bibTags 
                    ON bib.id=bibTags.bibId 
                JOIN tags 
                    ON bibTags.tagId=tags.id 
                WHERE 
                    bib.citeKey=?
            """,(citeKey,))
            return self._unwrapFirst(cur.fetchall())


    def modBibtex(self, searchCiteKey, collection):
        tags = self.getTags(searchCiteKey)
        with SqlCursor(self.dbFile) as cur:
            cur.execute("SELECT pdfMd5,pmid FROM bib WHERE citeKey=?", (searchCiteKey,))
            row = cur.fetchone()
            pdfMd5, pmid = row
        abstract = collection.entries[searchCiteKey].fields['annote']
        self.delBibtex(searchCiteKey)
        self.addBibtex(collection, pdfMd5, abstract, pmid, tags=tags)


    def addBibtex(self, collection, pdfMd5, abstract, pmid, tags=None):
        """Only first entry added"""
        tags = tags or []
        with SqlCursor(self.dbFile) as cur:
            for citekey, bib in collection.entries.items():
                fields = {"bk_"+k : v for k,v in bib.fields.items()}
                if abstract:
                    fields['bk_annote'] = abstract
                if pmid:
                    fields['pmid'] = pmid
                fields['pdfMd5'] = pdfMd5
                fields['citeKey'] = citekey
                fields['entryType'] = bib.type
                fields['addDate'] = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

                people = dict(author=[], editor=[])
                for k, ps in bib.persons.items():
                    for p in ps:
                        first = ' '.join(p.first_names)
                        middle = ' '.join(p.middle_names)
                        last = ' '.join(p.last_names)
                        pid = self._lookupPerson(cur, first, middle, last)
                        people[k].append(pid)

                tagIds = [self._lookupTag(cur, t) for t in tags]

                cols = list(fields.keys())
                vals = [fields[c] for c in cols]
                cur.execute("INSERT INTO bib({}) VALUES({})".format(', '.join(cols), ', '.join(['?']*len(cols))), vals)
                bibId = cur.lastrowid
                cur.executemany("INSERT INTO authors(bibId, personId) VALUES(?, ?)", [(bibId,a) for a in people['author']])
                cur.executemany("INSERT INTO editors(bibId, personId) VALUES(?, ?)", [(bibId,a) for a in people['editor']])
                cur.executemany("INSERT INTO bibTags(bibId, tagId) VALUES(?, ?)", [(bibId,a) for a in tagIds])
                return


    def lookup(self, key, value):
        with SqlCursor(self.dbFile) as cur:
            ids = self._lookupBibId(cur, key, value)
            return self._dictsToBib([self._bibDataById(cur,bibId) for bibId in ids])

    def getAllKeys(self):
        with SqlCursor(self.dbFile) as cur:
            cur.execute("SELECT bib.citeKey FROM bib", ())
            return self._unwrapFirst(cur.fetchall())

    def getAll(self):
        with SqlCursor(self.dbFile) as cur:
            cur.execute("SELECT bib.id FROM bib", ())
            ids = self._unwrapFirst(cur.fetchall())
            return self._dictsToBib([self._bibDataById(cur,bibId) for bibId in ids])

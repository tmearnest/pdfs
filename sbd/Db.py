import sqlite3, logging, os, contextlib, datetime
from pybtex.database import parse_file, BibliographyData, Entry, Person
from distutils.spawn import find_executable


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
                                 doi TEXT,
                                 pdfMd5 TEXT,
                                 addDate TEXT,
                                 entryType TEXT,
                                 address TEXT,
                                 annote TEXT,
                                 booktitle TEXT,
                                 chapter TEXT,
                                 crossref TEXT,
                                 edition TEXT,
                                 howpublished TEXT,
                                 institution TEXT,
                                 journal TEXT,
                                 key TEXT,
                                 month TEXT,
                                 note TEXT,
                                 number TEXT,
                                 organization TEXT,
                                 pages TEXT,
                                 publisher TEXT,
                                 school TEXT,
                                 series TEXT,
                                 title TEXT,
                                 type TEXT,
                                 volume TEXT,
                                 year TEXT)
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
    def _lookupPerson(cur, first,  middle, last):
        cur.execute("SELECT * FROM people WHERE first=? and middle=? and last=?",(first,middle,last) )
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO people(first,middle,last) VALUES(?,?,?)", (first,middle,last))
            return cur.lastrowid
        else:
            return row[0]


    @staticmethod
    def _findTag(cur,tag):
        cur.execute("SELECT * FROM tags WHERE tag=?",(tag,))
        row = cur.fetchone()
        if row is None:
            return None
        else:
            return row[0]


    def _lookupTag(self,cur, tag):
        tag = tag.lower()
        tid = self._findTag(cur,tag)
        if tid is None:
            cur.execute("INSERT INTO tags(tag) VALUES(?)", (tag,))
            return cur.lastrowid
        else:
            return tid

    def modTags(self, citeKey, tagDiff):
        addTags = [x[1:] if x[0] == '+' else x for x in tagDiff if x[0] != '-']
        delTags = [x[1:] for x in tagDiff if x[0] == '-']
        bibId = self._bibIdFromCiteKey(citeKey)[0]
        
        with SqlCursor(self.dbFile) as cur:
            for tag in delTags:
                tid = self._findTag(cur, tag)
                if tid is None:
                    perror("Tag {} not found".format(tag))
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
        for bibId in self._bibIdFromCiteKey(searchCiteKey):
            with SqlCursor(self.dbFile) as cur:
                def tagset(table, field, selField, val):
                    cur.execute("SELECT {field} FROM {table} "
                                "WHERE {selField}=?".format(table=table,field=field,selField=selField), (val,))
                    return set(self._unwrapIds(cur.fetchall()))

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
                    arow = cur.fetchone()
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
            cur.execute("SELECT tag FROM bib JOIN bibTags ON bib.id=bibTags.bibId JOIN tags on bibTags.tagId=tags.id WHERE bib.citeKey=?",(citeKey,))
            return self._unwrapIds(cur.fetchall())

    def modBibtex(self, searchCiteKey, collection):
        tags = self.getTags(searchCiteKey)
        with SqlCursor(self.dbFile) as cur:
            cur.execute("SELECT pdfMd5 FROM bib WHERE citeKey=?", (searchCiteKey,))
            row = cur.fetchone()
            pdfMd5 = row[0]
        self.delBibtex(searchCiteKey)
        self.addBibtex(collection, pdfMd5, tags=tags)


    def addBibtex(self, collection, pdfMd5, tags=[]):
        """Only first entry added"""
        with SqlCursor(self.dbFile) as cur:
            for citekey, bib in collection.entries.items():
                entryType = bib.type
                fields = dict(bib.fields)
                fields['pdfMd5'] = pdfMd5
                people = dict(author=[], editor=[])
                for k, ps in bib.persons.items():
                    for p in ps:
                        first = ' '.join(p.first_names)
                        middle = ' '.join(p.middle_names)
                        last = ' '.join(p.last_names)
                        pid = self._lookupPerson(cur, first, middle, last)
                        people[k].append(pid)

                tagIds = [self._lookupTag(cur, t) for t in tags]

                fields['citeKey'] = citekey
                fields['entryType'] = entryType
                fields['addDate'] = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())

                cols = list(fields.keys())
                vals = [fields[c] for c in cols]
                cur.execute("INSERT INTO bib({}) VALUES({})".format(', '.join(cols), ', '.join(['?']*len(cols))), vals)
                bibId = cur.lastrowid
                cur.executemany("INSERT INTO authors(bibId, personId) VALUES(?, ?)", [(bibId,a) for a in people['author']])
                cur.executemany("INSERT INTO editors(bibId, personId) VALUES(?, ?)", [(bibId,a) for a in people['editor']])
                cur.executemany("INSERT INTO bibTags(bibId, tagId) VALUES(?, ?)", [(bibId,a) for a in tagIds])
                return

    @staticmethod
    def _unwrapIds(rs):
        return [x[0] for x in rs]

    def _lookupBibIdPerson(self, key, value):
        with SqlCursor(self.dbFile) as cur:
            sql = """
                SELECT bib.id
                FROM bib
                JOIN {key} ON {key}.bibId==bib.id
                JOIN people ON people.id=={key}.personId
                WHERE people.first like "%{value}%" OR people.middle like "%{value}%" OR people.last like "%{value}%"
            """.format(key=key, value=value)
            cur.execute(sql)
            return self._unwrapIds(cur.fetchall())

    def _bibIdFromCiteKey(self, value):
        with SqlCursor(self.dbFile) as cur:
            cur.execute("SELECT bib.id FROM bib WHERE bib.citeKey==?", (value,))
            return self._unwrapIds(cur.fetchall())

    def _lookupBibId(self, key, value):
        if key=='authors':
            return self._lookupBibIdPerson('authors', value)
        elif key=='editors':
            return self._lookupBibIdPerson('editors', value)
        elif key=='tag':
            with SqlCursor(self.dbFile) as cur:
                cur.execute("""
                    SELECT bib.id
                    FROM bib
                    JOIN bibTags ON bibTags.bibId==bib.id
                    JOIN tags ON tags.id==bibTags.tagId
                    WHERE tags.tag=?
                """, (value,))
                return self._unwrapIds(cur.fetchall())
        else:
            with SqlCursor(self.dbFile) as cur:
                cur.execute('SELECT bib.id FROM bib WHERE bib.{key} LIKE "%{value}%"'.format(key=key,value=value))
                return self._unwrapIds(cur.fetchall())

    def lookup(self, key, value):
        ids = self._lookupBibId(key, value)
        with SqlCursor(self.dbFile) as cur:
            return self._dictsToBib([self._bibDataById(cur,bibId) for bibId in ids])

    def getAll(self):
        with SqlCursor(self.dbFile) as cur:
            cur.execute("SELECT bib.id FROM bib", ())
            ids = self._unwrapIds(cur.fetchall())
            return self._dictsToBib([self._bibDataById(cur,bibId) for bibId in ids])

    def _dictsToBib(self, ds):
        db = BibliographyData()
        empty = True
        for d in ds:
            empty = False
            bib = Entry(d['entryType'])
            if len(d['authors']) > 0:
                bib.persons['author'] = [Person(" ".join(ns)) for ns in d['authors']]
            if len(d['editors']) > 0:
                bib.persons['editor'] = [Person(" ".join(ns)) for ns in d['editors']]

            for k,v in d.items():
                if k not in ['authors', 'editors', 'entryType', 'citeKey', 'id', 'pdfMd5']:
                    if v is not None:
                        bib.fields[k] = v
            db.add_entry(d['citeKey'], bib)
        return None if empty else db
            
    def _bibDataById(self, cur, bibId):
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


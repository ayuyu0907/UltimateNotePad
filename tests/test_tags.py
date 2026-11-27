"""Tag regression tests. Run only this module: python3 -m unittest tests.test_tags -v"""
import contextlib
import io
import os
from pathlib import Path
import runpy
import shutil
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from html.parser import HTMLParser

from app import app, load_notes, load_note_tags, connect_db

ROOT = Path(__file__).resolve().parents[1]


class NoteRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if 'unp-note-row' in data.get('class', '').split() and 'data-unp-note-id' in data:
            self.ids.append(int(data['data-unp-note-id']))


class TagTests(unittest.TestCase):
    def setUp(self):
        original = Path.cwd()
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(os.chdir, original)
        os.chdir(temp.name)
        Path('data').mkdir()
        Path('migrations').mkdir()
        self.migration = Path('migrations/003_add_tags.py').resolve()
        shutil.copyfile(ROOT / 'migrations/003_add_tags.py', self.migration)
        with contextlib.closing(sqlite3.connect('data/notes.db')) as c, c:
            c.execute('''CREATE TABLE notes (
              id INTEGER PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              is_pinned INTEGER NOT NULL DEFAULT 0, is_favorite INTEGER NOT NULL DEFAULT 0)''')
            c.executemany('INSERT INTO notes VALUES (?,?,?,?,?,?,?)', [
                (1,'Python','学習','2026-11-20 10:00:00','2026-11-20 10:00:00',0,0),
                (2,'Flask','学習','2026-11-21 10:00:00','2026-11-21 10:00:00',0,1),
                (3,'SQLite','学習','2026-11-22 10:00:00','2026-11-22 10:00:00',1,1),
                (4,'JavaScript','開発','2026-11-23 10:00:00','2026-11-23 10:00:00',1,0),
            ])
        self.migrate()
        self.client = app.test_client()
        self.a = self.create('学習')
        self.b = self.create('開発','#aabbcc')
        for note, tag in [(1,self.a),(2,self.a),(3,self.a),(3,self.b),(4,self.b)]:
            self.assign(note,tag,1)

    def migrate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(self.migration))

    def create(self,name,color='#64748b'):
        response=self.client.post('/tags/create',data={'name':name,'color':color})
        self.assertEqual(response.status_code,201,response.get_data(as_text=True))
        self.assertTrue(response.json['ok'])
        return response.json['id']

    def assign(self,note,tag,value):
        response=self.client.post(f'/notes/{note}/tags/{tag}',data={'assigned':value})
        self.assertEqual(response.status_code,200,response.get_data(as_text=True))
        self.assertEqual(response.json['assigned'],value)

    def ids(self,**kwargs):
        return [n['id'] for n in load_notes(**kwargs)]

    def state(self,note=None):
        query={} if note is None else {'note_id':note}
        r=self.client.get('/api/tags',query_string=query)
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['ok'])
        return r.json

    def rows(self,url='/',query=None):
        r=self.client.get(url,query_string=query)
        self.assertEqual(r.status_code,200,r.get_data(as_text=True)[:500])
        parser=NoteRows();parser.feed(r.get_data(as_text=True));return parser.ids

    def test_migration_idempotent(self):
        self.migrate()
        self.assertEqual(len(self.state()['tags']),2)
        self.assertEqual(set(self.state(3)['assigned']),{self.a,self.b})
        with contextlib.closing(connect_db()) as c:
            self.assertEqual(c.execute('PRAGMA foreign_keys').fetchone()[0],1)
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_tag_create_and_edit(self):
        tag=self.create('  Python  ','#ABCDEF')
        row=next(t for t in self.state()['tags'] if t['id']==tag)
        self.assertEqual((row['name'],row['color']),('Python','#abcdef'))
        r=self.client.post(f'/tags/{tag}/update',data={'name':'Python 3','color':'#123456'})
        self.assertEqual(r.status_code,200)
        row=next(t for t in self.state()['tags'] if t['id']==tag)
        self.assertEqual((row['name'],row['color']),('Python 3','#123456'))

    def test_tag_name_unique(self):
        self.assertEqual(self.client.post('/tags/create',data={'name':' 学習 '}).status_code,409)
        self.assertEqual(self.client.post(f'/tags/{self.b}/update',data={'name':'学習'}).status_code,409)
        self.create('python'); self.create('Python')  # case-sensitive UNIQUE

    def test_invalid_tag_fields(self):
        for data in ({'name':''},{'name':' '*3},{'name':'x'*41},{'name':'x\ny'},{'name':'new','color':'red'},{'name':'new','color':'#fff'}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post('/tags/create',data=data).status_code,400)
                self.assertEqual(self.client.post(f'/tags/{self.a}/update',data=data).status_code,400)
        self.assertEqual(len(self.state()['tags']),2)
        self.assertEqual(next(t for t in self.state()['tags'] if t['id']==self.a)['name'],'学習')

    def test_assignment_idempotent_and_independent(self):
        before=load_notes()
        for _ in range(2): self.assign(1,self.b,1)
        self.assertEqual(set(self.state(1)['assigned']),{self.a,self.b})
        for _ in range(2): self.assign(1,self.b,0)
        self.assertEqual(self.state(1)['assigned'],[self.a])
        self.assertEqual(set(self.state(3)['assigned']),{self.a,self.b})
        self.assertEqual(load_notes(),before)  # no title, timestamp, pin or favorite changes

    def test_tag_filter_and_sort(self):
        self.assertEqual(self.ids(tag_id=self.a),[3,2,1])
        self.assertEqual(self.ids(tag_id=self.a,sort='old'),[3,1,2])
        self.assertEqual(self.ids(tag_id=self.a,sort='title'),[3,2,1])
        self.assertEqual(self.ids(tag_id=self.b),[4,3])
        self.assertEqual(self.ids(tag_id=self.a,favorite_only=True),[3,2])
        self.assertEqual(self.ids(tag_id=self.a,favorite_only=True,keyword='Flask'),[2])
        self.assertEqual(self.ids(tag_id=self.a,keyword='開発'),[])
        self.assertEqual(self.ids(tag_id=self.b,keyword='JavaScript',favorite_only=True),[])
        self.assertEqual(self.ids(),[4,3,2,1])

    def test_page_filter_and_template(self):
        self.assertEqual(self.rows(query={'tag':self.a,'favorite':1,'q':'学習','sort':'old'}),[3,2])
        self.assertEqual(self.rows(query={'tag':self.b,'sort':'old'}),[3,4])
        self.assertEqual(self.rows(query={'tag':999}),[4,3,2,1])
        self.assertEqual(self.rows(query={'tag':'bad'}),[4,3,2,1])
        r=self.client.get('/',query_string={'tag':self.a,'id':3})
        self.assertIn('id="unp-editor-tags" data-note-id="3"',r.get_data(as_text=True))
        self.assertIn('id="unp-tag-dialog"',r.get_data(as_text=True))

    def test_batch_relationships(self):
        tags=load_note_tags([1,2,3,4,999])
        self.assertEqual({t['id'] for t in tags[3]},{self.a,self.b})
        self.assertEqual(tags[999],[])
        self.assertEqual(load_note_tags([]),{})
        self.assertEqual(len(load_note_tags(range(1,1002))),1001)

    def test_delete_tag_cascades_only_relationships(self):
        before=load_notes()
        self.assertEqual(self.client.post(f'/tags/{self.a}/delete').status_code,200)
        self.assertEqual(load_notes(),before)
        self.assertEqual(self.state(1)['assigned'],[])
        self.assertEqual(self.state(3)['assigned'],[self.b])
        self.assertEqual(self.rows(query={'tag':self.a}),[4,3,2,1])
        with contextlib.closing(connect_db()) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM note_tags WHERE tag_id=?',(self.a,)).fetchone()[0],0)

    def test_delete_note_cascades(self):
        self.assertEqual(self.client.post('/notes/3/delete').status_code,302)
        self.assertFalse(self.state(3)['note_exists'])
        self.assertEqual(len(self.state()['tags']),2)
        self.assertEqual(self.ids(tag_id=self.a),[2,1])
        with contextlib.closing(connect_db()) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM note_tags WHERE note_id=3').fetchone()[0],0)
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_invalid_assignment_and_not_found(self):
        for data in ({},{'assigned':2},{'assigned':'abc'}):
            self.assertEqual(self.client.post(f'/notes/1/tags/{self.b}',data=data).status_code,400)
        for url in (f'/notes/999/tags/{self.a}','/notes/1/tags/999'):
            self.assertEqual(self.client.post(url,data={'assigned':1}).status_code,404)
        self.assertEqual(self.client.post('/tags/999/update',data={'name':'x'}).status_code,404)
        self.assertEqual(self.client.post('/tags/999/delete').status_code,404)
        self.assertEqual(self.client.get('/tags/create').status_code,405)
        self.assertEqual(self.client.get(f'/notes/1/tags/{self.a}').status_code,405)
        self.assertEqual(self.state(1)['assigned'],[self.a])

    def test_escaping_and_parameterization(self):
        tag=self.create('<script>alert(1)</script>')
        self.assign(1,tag,1)
        text=self.client.get('/',query_string={'id':1}).get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>',text)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',text)
        self.create("x'); DROP TABLE notes;--")
        self.assertEqual(len(load_notes()),4)

    def test_existing_pin_favorite_and_autosave(self):
        self.assertEqual(self.client.post('/notes/1/pin').status_code,302)
        self.assertEqual(self.client.post('/notes/1/favorite',data={'is_favorite':1}).status_code,302)
        self.assertEqual(self.ids(tag_id=self.a,favorite_only=True,sort='old'),[1,3,2])
        r=self.client.post('/notes/1/update',data={'title':'Changed','content':'New body'},headers={'X-Requested-With':'XMLHttpRequest'})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json['success'])
        self.assertEqual(self.state(1)['assigned'],[self.a])


if __name__ == '__main__':
    unittest.main()

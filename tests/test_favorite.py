import os
import sqlite3
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory
from app import app, load_notes


def setup_test_db():

    connection = None

    try:
        connection = sqlite3.connect("data/notes.db")
        cursor = connection.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_pinned INTEGER NOT NULL DEFAULT 0,
            is_favorite INTEGER NOT NULL DEFAULT 0
        )
        ''')

        items = [
            (1, "Python", "Python学習", "2026-11-20 10:00:00", "2026-11-20 10:00:00", 0, 0),
            (2, "Flask", "Flask学習", "2026-11-21 10:00:00", "2026-11-21 10:00:00", 0, 1),
            (3, "SQLite", "SQLite学習", "2026-11-22 10:00:00", "2026-11-22 10:00:00", 1, 1),
            (4, "JavaScript", "JavaScript学習", "2026-11-23 10:00:00", "2026-11-23 10:00:00", 1, 0)
        ]

        cursor.executemany(
            "INSERT INTO notes (id, title, content, created_at, updated_at, is_pinned, is_favorite) VALUES (?, ?, ?, ?, ?, ?, ?)",
            items
        )

        connection.commit()

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()

def get_favorite_status(note_id):
    connection = None

    try:
        connection = sqlite3.connect("data/notes.db")
        cursor = connection.cursor()

        cursor.execute("SELECT is_favorite FROM notes WHERE id = ?", (note_id,))
        result = cursor.fetchone()

        return result[0] if result else None

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()



class FavoriteTests(unittest.TestCase):

    def setUp(self):
        original_dir = Path.cwd()

        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.addCleanup(os.chdir, original_dir)

        os.chdir(temp_dir.name)
        Path("data").mkdir()

        setup_test_db()

        self.client = app.test_client()

    def test_setup(self):
        notes = load_notes()

        self.assertEqual(len(notes), 4)


    def test_add_favorite(self):
        self.assertEqual(get_favorite_status(1), 0)

        response = self.client.post(
            "/notes/1/favorite",
            data={"is_favorite": 1}
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(get_favorite_status(1), 1)

    def test_remove_favorite(self):
        self.assertEqual(get_favorite_status(2), 1)

        response = self.client.post(
            "/notes/2/favorite",
            data={"is_favorite": 0}
        )

        self.assertEqual(response.status_code, 302)

        self.assertEqual(get_favorite_status(2), 0)

    def test_favorite_idempotency(self):

        response = self.client.post("/notes/1/favorite", data={"is_favorite": 1})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_favorite_status(1), 1)

        response = self.client.post("/notes/1/favorite", data={"is_favorite": 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_favorite_status(1), 1)



    def test_favorite_filter(self):
        # ① 通常の一覧
        # 期待値：[4, 3, 2, 1]
        ids = [note["id"] for note in load_notes()]
        self.assertEqual(ids, [4, 3, 2, 1])
        

        # ② お気に入りのみ
        # 期待値：[3, 2]
        ids = [note["id"] for note in load_notes(favorite_only=True)]
        self.assertEqual(ids, [3, 2])

    def test_favorite_search(self):
        # ③ お気に入りからFlaskを検索
        # 期待値：[2]
        notes = load_notes(
            keyword="Flask",
            favorite_only=True
        )

        ids = [note["id"] for note in notes]
        self.assertEqual(ids, [2])

        # ④ お気に入りからPythonを検索
        # 期待値：[]
        notes = load_notes(
            keyword="Python",
            favorite_only=True
        )

        ids = [note["id"] for note in notes]
        self.assertEqual(ids, [])

        # ⑤ お気に入りから「学習」を検索
        # 期待値：[3, 2]
        notes = load_notes(
            keyword="学習",
            favorite_only=True
        )

        ids = [note["id"] for note in notes]
        self.assertEqual(ids, [3, 2])


    def test_favorite_sort(self):
        # ① ID 1をお気に入りに登録
        # POSTリクエストを送信
        response = self.client.post("/notes/1/favorite", data={"is_favorite": 1})

        # ② HTTP 302を確認
        self.assertEqual(response.status_code, 302)

        # ③ 新しい順
        # 期待値：[3, 2, 1]
        self.assertEqual([note["id"] for note in load_notes(sort="new", favorite_only=True)], [3, 2, 1])

        # ④ 古い順
        # 期待値：[3, 1, 2]
        self.assertEqual([note["id"] for note in load_notes(sort="old", favorite_only=True)], [3, 1, 2])

        # ⑤ タイトル順
        # 期待値：[3, 2, 1]
        self.assertEqual([note["id"] for note in load_notes(sort="title", favorite_only=True)], [3, 2, 1])


    def test_invalid_favorite_value(self):
        # ① 不正な値をリストにまとめる
        values = [2, -1, "abc"]

        # ② forとsubTestを使って検証
        for value in values:
            with self.subTest(value=value):
                response = self.client.post("/notes/1/favorite", data={"is_favorite": value})

                # ④ HTTP 400を確認
                self.assertEqual(response.status_code, 400)

                # ⑤ ID 1のお気に入り状態が0のままか確認
                self.assertEqual(get_favorite_status(1), 0)

        # ③ POSTリクエストを送信
        response = self.client.post("/notes/1/favorite", data={"is_favorite": 2})

        # ④ HTTP 400を確認
        self.assertEqual(response.status_code, 400)

        # ⑤ ID 1のお気に入り状態が0のままか確認
        self.assertEqual(get_favorite_status(1), 0)


    def test_missing_favorite_value(self):
        # ⑥ データを指定せずPOST
        response = self.client.post("/notes/1/favorite")

        # ⑦ HTTP 400を確認
        self.assertEqual(response.status_code, 400)

        # ⑧ DBの状態が変更されていないか確認
        self.assertEqual(get_favorite_status(1), 0)


    def test_favorite_not_found(self):
        # ⑨ 存在しないID 999にPOST
        # is_favorite=1
        response = self.client.post("/notes/999/favorite", data={"is_favorite": 1})

        # ⑩ HTTP 404を確認
        self.assertEqual(response.status_code, 404)

        # ⑪ メモが新規作成されていないか確認
        self.assertEqual(get_favorite_status(999), None)


    def test_favorite_method_not_allowed(self):
        # ⑫ ID 1のお気に入りURLにGET
        response = self.client.get("/notes/1/favorite")

        # ⑬ HTTP 405を確認
        self.assertEqual(response.status_code, 405)

        # ⑭ DBの状態が変更されていないか確認
        self.assertEqual(get_favorite_status(1), 0)



if __name__ == "__main__":
    unittest.main()

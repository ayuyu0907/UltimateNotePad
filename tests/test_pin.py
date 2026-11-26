#!/workspaces/UltimateNotePad/.venv/bin/python3

import os
import sqlite3

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
            is_pinned INTEGER NOT NULL DEFAULT 0
        )
        ''')

        items = [
            (1, "Python", "Python学習", "2026-11-20 10:00:00", "2026-11-20 10:00:00", 0),
            (2, "Flask", "Flask学習", "2026-11-21 10:00:00", "2026-11-21 10:00:00", 0),
            (3, "SQLite", "SQLite学習", "2026-11-22 10:00:00", "2026-11-22 10:00:00", 1)
        ]

        cursor.executemany(
            "INSERT INTO notes (id, title, content, created_at, updated_at, is_pinned) VALUES (?, ?, ?, ?, ?, ?)",
            items
        )

        connection.commit()

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()

def get_pin_status(note_id):
    connection = None

    try:
        connection = sqlite3.connect("data/notes.db")
        cursor = connection.cursor()

        cursor.execute("SELECT is_pinned FROM notes WHERE id = ?", (note_id,))
        result = cursor.fetchone()

        return result[0] if result else None

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()    


def test_toggle_pin():
    client = app.test_client()

    # ① 初期状態を確認
    assert get_pin_status(1) == 0

    # ② POSTリクエストを送信
    response = client.post("/notes/1/pin")
    
    # ③ HTTPステータスコードが302か確認
    assert response.status_code == 302

    # ④ DBのis_pinnedが1か確認
    assert get_pin_status(1) == 1
    print("ピン留めテスト成功")

    # ⑤ 再度POSTリクエストを送信
    response = client.post("/notes/1/pin")

    # ⑥ HTTPステータスコードが302か確認
    assert response.status_code == 302

    # ⑦ DBのis_pinnedが0か確認
    assert get_pin_status(1) == 0

    print("ピン留め解除テスト成功")


def test_sort():
    # ① 新しい順
    notes = load_notes(sort="new")
    ids = [note["id"] for note in notes]
    assert ids == [3, 2, 1]

    # ② 古い順
    notes = load_notes(sort="old")
    ids = [note["id"] for note in notes]
    assert ids == [3, 1, 2]

    # ③ タイトル順
    notes = load_notes(sort="title")
    ids = [note["id"] for note in notes]
    assert ids == [3, 2, 1]

    # ④ 存在しない並べ替え条件
    notes = load_notes(sort="invalid")
    ids = [note["id"] for note in notes]
    assert ids == [3, 2, 1] 

    print("並べ替えテスト成功")


def test_search():
    # ⑤ Pythonを検索
    # 期待するID：[1]
    notes = load_notes(keyword="Python")
    ids = [note["id"] for note in notes]
    assert ids == [1]

    # ⑥ 学習を検索
    # sort="old"
    # 期待するID：[3, 1, 2]
    notes = load_notes(keyword="学習", sort="old")
    ids = [note["id"] for note in notes]
    assert ids == [3, 1, 2]

    # ⑦ 存在しないキーワード
    # 期待する結果：[]
    notes = load_notes(keyword="存在しないキーワード")
    ids = [note["id"] for note in notes]
    assert ids == []

    print("検索テスト成功")


def test_invalid_pin():
    client = app.test_client()

    # ⑧ 存在しないID（999）をPOST
    # 期待するステータス：404
    response = client.post("/notes/999/pin")
    assert response.status_code == 404

    # ⑨ ピン留めURLにGETでアクセス
    # 期待するステータス：405
    response = client.get("/notes/1/pin")
    assert response.status_code == 405

    print("異常系テスト成功")


def main():
    original_dir = Path.cwd()

    with TemporaryDirectory() as temp_dir:
        try:
            os.chdir(temp_dir)

            Path("data").mkdir()

            setup_test_db()
            print("テストDBの準備完了")

            test_toggle_pin()
            test_sort()
            test_search()
            test_invalid_pin()

            print("すべてのテストが成功しました！")
            
        finally:
            os.chdir(original_dir)


if __name__ == "__main__":
    main()
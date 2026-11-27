from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "notes.db"

connection = None

try:
    if not DB_PATH.is_file():
        raise FileNotFoundError("データベースが見つかりません")

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(notes)")

    if not cursor.fetchall():
        raise RuntimeError("notesテーブルが存在しません")

    # トランザクション開始
    cursor.execute("BEGIN")

    # タグ管理テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#64748b',
            created_at TEXT NOT NULL
        )
    """)

    # メモとタグの中間テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,

            PRIMARY KEY (note_id, tag_id),

            FOREIGN KEY (note_id)
                REFERENCES notes(id)
                ON DELETE CASCADE,

            FOREIGN KEY (tag_id)
                REFERENCES tags(id)
                ON DELETE CASCADE
        )
    """)

    # タグからメモを検索するためのインデックス
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_note_tags_tag_id
        ON note_tags(tag_id)
    """)

    connection.commit()

    print("タグ機能のマイグレーションが完了しました")

except sqlite3.Error as error:
    print(f"データベースエラー: {error}")

    if connection is not None:
        connection.rollback()

    raise

finally:
    if connection is not None:
        connection.close()

#!/workspaces/UltimateNotePad/.venv/bin/python3

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = None

try:
    keyword = input("検索キーワード: ")
    pattern = f"%{keyword}%"

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, title FROM notes WHERE title LIKE ? OR content LIKE ?",
        (pattern, pattern,)
    )

    rows = cursor.fetchall()
    if rows:
        for note_id, title in rows:
            print(f"ID: {note_id} | {title}")
    else:
        print("該当するメモはありません")

except sqlite3.Error as error:
    print(f"データベースエラー: {error}")

finally:
    if connection is not None:
        connection.close()
    pass

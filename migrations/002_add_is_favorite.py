#!/workspaces/UltimateNotePad/.venv/bin/python3

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "notes.db"

connection = None

try:
    if not DB_PATH.exists():
        raise FileNotFoundError("データベースが見つかりません")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(notes)")
    columns = cursor.fetchall()
    if not columns:
        raise RuntimeError("notesテーブルが存在しません")

    column_names = [column[1] for column in columns]

    if "is_favorite" not in column_names:
        cursor.execute(
            "ALTER TABLE notes ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0;",
        )
    else:
        print("is_favoriteはすでに存在します")

    connection.commit()

except sqlite3.Error as error:
    print(f"データベースエラー: {error}")
    raise

finally:
    if connection is not None:
        connection.close()

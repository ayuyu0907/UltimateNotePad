#!/workspaces/UltimateNotePad/.venv/bin/python3

from pathlib import Path
import sqlite3

DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "notes.db"
)

connection = None

try:
    note_id = int(input("確認するメモID: "))

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM notes WHERE id = ?",
        (note_id,)
    )

    row = cursor.fetchone()
    if row is None:
        print("削除済み")
    else:
        print("まだ存在する")

except ValueError:
    print("整数で入力してください。")

except sqlite3.Error as error:
    print(f"データベースエラー: {error}")

finally:
    if connection is not None:
        connection.close()
    pass

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



    connection.commit()

except sqlite3.Error as error:
    print(f"データベースエラー: {error}")
    raise

finally:
    if connection is not None:
        connection.close()

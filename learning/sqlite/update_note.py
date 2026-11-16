#!/workspaces/UltimateNotePad/.venv/bin/python3

from datetime import datetime
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

cursor.execute(
    "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
    (
        "UPDATEの練習",
        "SQLiteから編集できました！",
        now_str,
        2
    )
)

connection.commit()
connection.close()
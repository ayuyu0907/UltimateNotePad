#!/workspaces/UltimateNotePad/.venv/bin/python3

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute(
    "SELECT * FROM notes ORDER BY updated_at DESC;"
)

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()

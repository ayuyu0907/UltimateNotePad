#!/workspaces/UltimateNotePad/.venv/bin/python3

from datetime import datetime
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

cursor.execute(
    "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
    ("we are Party TONIGHT!!!", "First adadada Club", now_str, now_str)
)

connection.commit()
connection.close()
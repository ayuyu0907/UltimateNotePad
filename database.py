#!/workspaces/UltimateNotePad/.venv/bin/python3

import sqlite3

connection = sqlite3.connect("data/notes.db")
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
""")

connection.close()
#!/workspaces/UltimateNotePad/.venv/bin/python3

# 1. 必要なモジュールをimport

from pathlib import Path
import sqlite3

# 2. データベースに接続

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# 3. input() でIDを取得
note_id = int(input("削除するメモID: "))

# 4. DELETEを実行
cursor.execute(
    "DELETE FROM notes WHERE id = ?"
    (note_id)
)

# 5. rowcountで結果を確認
rows = cursor.rowcount

if rows > 0:
    print("メモを削除しました")
else:
    print("メモが見つかりません")


# 6. commitして接続を閉じる

connection.commit()
connection.close()
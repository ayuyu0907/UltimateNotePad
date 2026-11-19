#!/workspaces/UltimateNotePad/.venv/bin/python3

from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = None

try:
    # IDを入力
    note_id = int(input("削除するメモID: "))
    # DBに接続
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    # DELETEを実行
    cursor.execute(
        "DELETE FROM notes WHERE id = ?",
        (note_id,)
    )

    connection.commit()

    # rowcountで削除件数を確認
    rows = cursor.rowcount

    if rows > 0:
        print("メモを削除しました")
    else:
        print("メモが見つかりません")

except ValueError:
    print("整数で入力してください。")

except sqlite3.Error as error:
    print("データベースでエラーが発生しました。")
    print(f"エラー: {error}")
finally:
    if connection is not None:
        connection.close()
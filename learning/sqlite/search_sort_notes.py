from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parent / "data" / "practice.db"

connection = None

try:
    keyword = input("検索キーワード: ")
    pattern = f"%{keyword}%"

    print("並べ替え方法を選択してください")
    print("1: 更新日時が新しい順")
    print("2: 更新日時が古い順")
    print("3: タイトル順")
    print("")

    choice = input("選択: ")

    if choice == "1":
        order = "updated_at DESC"
    elif choice == "2":
        order = "updated_at ASC"
    elif choice == "3":
        order = "title ASC"
    else:
        raise ValueError("無効な選択です")

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    sql = f"""
    SELECT id, title, updated_at
    FROM notes
    WHERE title LIKE ? OR content LIKE ?
    ORDER BY {order}
    LIMIT 5
    """

    cursor.execute(
        sql,
        (pattern, pattern,)
    )

    rows = cursor.fetchall()

    print("検索結果（最大5件）")
    if rows:
        for note_id, title, updated_at in rows:
            print(f"ID: {note_id} | {title} | {updated_at}")
    else:
        print("該当するメモはありません")

except ValueError as error:
    print(f"入力エラー: {error}")

except sqlite3.Error as error:
    print(f"データベースエラー: {error}")

finally:
    if connection is not None:
        connection.close()
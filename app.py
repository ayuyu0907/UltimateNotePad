#!/workspaces/UltimateNotePad/.venv/bin/python3

from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__) 


@app.route("/")
def index():

    # ① URLから検索条件を取得
    keyword = request.args.get("q", "")
    sort = request.args.get("sort", "new")

    # ② 検索・並べ替えを実行
    notes = load_notes(
        keyword=keyword,
        sort=sort
    )

    # ③ URLからメモIDを取得
    note_id = request.args.get(
        "id",
        default=None,
        type=int
    )

    selected_note = None

    if notes:

        if note_id is not None:
            for note in notes:
                if note["id"] == note_id:
                    selected_note = note
                    break
        if selected_note is None:
            selected_note = notes[0]
        
    return render_template(
        "index.html",
        notes=notes,
        selected_note=selected_note,
        keyword = keyword,
        sort = sort
    )

@app.route("/notes/create", methods=["POST"])
def create_note():
    
    title = request.form.get("title", "")
    title = title.strip()

    content = request.form.get("content", "")

    if not title:
        return "タイトルを入力してください", 400
    else:
        connection = sqlite3.connect("data/notes.db")
        cursor = connection.cursor()

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, content, now_str, now_str)
        )

        new_id = cursor.lastrowid

        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for("index", id=new_id))

@app.route("/notes/<int:note_id>/update", methods=["POST"])
def update_note(note_id):

    title = request.form.get("title", "")
    title = title.strip()

    content = request.form.get("content", "")

    if not title:
        return "タイトルを入力してください", 400
    else:
        connection = sqlite3.connect("data/notes.db")
        cursor = connection.cursor()

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
        "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
        (title, content, now_str, note_id)
        )

        affected_rows = cursor.rowcount
        if affected_rows == 0:
            cursor.close()
            connection.close()
            return "404 Not Found", 404    

        connection.commit()
        cursor.close()
        connection.close()

        is_ajax = (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
        )

        if is_ajax:
            return jsonify({
                "success": True,
                "note_id": note_id,
                "message": "保存成功！"
            })
        else:
            return redirect(url_for("index", id=note_id))
        

@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):

    connection = None

    try:
        connection = sqlite3.connect("data/notes.db")
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM notes WHERE id = ?",
            (note_id,)
        )

        connection.commit()

        rows = cursor.rowcount
        if rows == 0:
            return "メモが見つかりません", 404

        return redirect(url_for("index"))

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")

        if connection is not None:
            connection.rollback()

        return "データベースエラーが発生しました", 500

    finally:
        if connection is not None:
            connection.close()

def load_notes(keyword="", sort="new"):

    connection = None

    sort_options = {
    "new": "updated_at DESC",
    "old": "updated_at ASC",
    "title": "title ASC"
    }
    pattern = f"%{keyword}%"

    order = sort_options.get(sort, "updated_at DESC")


    try:
        connection = sqlite3.connect("data/notes.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        sql = f"""
        SELECT *
        FROM notes
        WHERE title LIKE ? OR content LIKE ?
        ORDER BY {order}
        """

        cursor.execute(
            sql,
            (pattern, pattern,)
        )

        rows = cursor.fetchall()
        notes = [dict(row) for row in rows]

        return notes

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()
            

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=3000,
        debug=True
    )
    
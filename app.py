#!/workspaces/UltimateNotePad/.venv/bin/python3

from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__) 

@app.route("/")
def index():

    notes = load_notes()
    
    selected_note = None

    note_id = request.args.get("id", default=1, type=int)

    for note in notes:
        if note["id"] == note_id:
            selected_note = note
            break
    
    return render_template(
        'index.html',
        notes=notes,
        selected_note=selected_note
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
            return "4o4 Not Found", 404    

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
        

def load_notes():
    connection = sqlite3.connect("data/notes.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
    "SELECT * FROM notes ORDER BY updated_at DESC;"
    )

    rows = cursor.fetchall()

    note_list = []
    for row in rows:
        note_list.append(dict(row))

    connection.close()

    return note_list

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=3000,
        debug=True
    )
    
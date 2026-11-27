from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import sqlite3
import re
from contextlib import closing

app = Flask(__name__) 


@app.route("/")
def index():

    # ① URLから検索条件を取得
    keyword = request.args.get("q", "")
    sort = request.args.get("sort", "new")
    favorite = request.args.get("favorite", default=0, type=int)
    favorite_only = favorite == 1
    tags = load_tags()
    tag_id = request.args.get("tag", default=0, type=int)
    if tag_id not in {tag["id"] for tag in tags}:
        tag_id = 0

    # ② 検索・並べ替えを実行
    notes = load_notes(
        keyword=keyword,
        sort=sort,
        favorite_only=favorite_only,
        tag_id=tag_id
    )
    note_tags = load_note_tags(note["id"] for note in notes)
    for note in notes:
        note["tags"] = note_tags[note["id"]]

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
        sort = sort,
        favorite_only=favorite_only,
        tag_id=tag_id,
        tags=tags
    )

@app.route("/notes/create", methods=["POST"])
def create_note():
    
    title = request.form.get("title", "")
    title = title.strip()

    content = request.form.get("content", "")

    if not title:
        return "タイトルを入力してください", 400
    else:
        connection = connect_db()
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
        connection = connect_db()
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
        connection = connect_db()
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

def load_notes(keyword="", sort="new", favorite_only=False, tag_id=0):
    
    connection = None

    sort_options = {
    "new": "updated_at DESC",
    "old": "updated_at ASC",
    "title": "title ASC"
    }
    pattern = f"%{keyword}%"

    order = sort_options.get(sort, "updated_at DESC")


    try:
        connection = connect_db()
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        sql = """
        SELECT *
        FROM notes
        WHERE (title LIKE ? OR content LIKE ?)
        """

        params = (pattern, pattern)

        if favorite_only:
            sql += " AND is_favorite = ?"
            params += (1,)
            
        if tag_id:
            sql += " AND EXISTS (SELECT 1 FROM note_tags WHERE note_id = notes.id AND tag_id = ?)"
            params += (tag_id,)

        sql += f" ORDER BY is_pinned DESC, {order}"

        cursor.execute(sql, params)

        rows = cursor.fetchall()
        notes = [dict(row) for row in rows]

        return notes

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        raise

    finally:
        if connection is not None:
            connection.close()


@app.route("/notes/<int:note_id>/favorite", methods=["POST"])
def set_favorite(note_id):

    is_favorite = request.form.get("is_favorite", type=int)

    if is_favorite not in [0, 1]:
        return "無効な値です", 400

    connection = None

    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE notes SET is_favorite = ? WHERE id = ?",
            (is_favorite, note_id)
        )

        rows = cursor.rowcount
        if rows == 0:
            return "メモが見つかりません", 404        

        connection.commit()
        return redirect(url_for("index", id=note_id))

    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")
        if connection is not None:
            connection.rollback()

        return "データベースエラーが発生しました", 500
    finally:
        if connection is not None:
            connection.close()

@app.route("/notes/<int:note_id>/pin", methods=["POST"])
def toggle_pin(note_id):

    connection = None

    try:
        connection = connect_db()
        cursor = connection.cursor()

        sql = """
        UPDATE notes
        SET is_pinned = CASE
            WHEN is_pinned = 1 THEN 0
            ELSE 1
        END
        WHERE id = ?;
        """

        cursor.execute(sql, (note_id,))

        rows = cursor.rowcount

        if rows == 0:
            return "メモが見つかりません", 404

        connection.commit()

        return redirect(url_for("index", id=note_id))
    
    except sqlite3.Error as error:
        print(f"データベースエラー: {error}")

        if connection is not None:
            connection.rollback()

        return "データベースエラーが発生しました", 500

    finally:
        if connection is not None:
            connection.close()
            
# UNP_TAGS_V1 — tag catalog and many-to-many relationships.
def connect_db():
    """Keep the existing relative DB path (including isolated lesson tests)."""
    connection = sqlite3.connect("data/notes.db")
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        return connection
    except BaseException:
        connection.close()
        raise


def safe_tag_color(value):
    return value.lower() if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) else "#64748b"


def tag_dict(row):
    item = dict(row)
    item["color"] = safe_tag_color(item["color"])
    return item


def load_tags():
    with closing(connect_db()) as connection:
        connection.row_factory = sqlite3.Row
        return [tag_dict(row) for row in connection.execute(
            "SELECT * FROM tags ORDER BY name COLLATE NOCASE, id"
        )]


def load_note_tags(note_ids):
    """Batch relationship lookups; do not query once per note."""
    ids = list(dict.fromkeys(note_ids))
    result = {note_id: [] for note_id in ids}
    if not ids:
        return result
    with closing(connect_db()) as connection:
        connection.row_factory = sqlite3.Row
        for start in range(0, len(ids), 400):
            batch = ids[start:start + 400]
            placeholders = ",".join("?" for _ in batch)
            sql = f"""
                SELECT nt.note_id, t.id, t.name, t.color, t.created_at
                FROM note_tags AS nt JOIN tags AS t ON t.id = nt.tag_id
                WHERE nt.note_id IN ({placeholders})
                ORDER BY t.name COLLATE NOCASE, t.id
            """
            for row in connection.execute(sql, batch):
                item = tag_dict(row)
                result[item.pop("note_id")].append(item)
    return result


def tag_error(code, status):
    return jsonify(ok=False, error=code), status


def tag_fields():
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "#64748b")
    if not 1 <= len(name) <= 40 or any(ord(char) < 32 or ord(char) == 127 for char in name):
        return None
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        return None
    return name, color.lower()


@app.get("/api/tags")
def tag_state():
    """The editor may be outside the active sidebar filter."""
    raw_id = request.args.get("note_id")
    note_id = request.args.get("note_id", type=int)
    if raw_id is not None and (note_id is None or not 1 <= note_id <= 2**63 - 1):
        return tag_error("invalid", 400)
    try:
        with closing(connect_db()) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN")
            tags = [tag_dict(row) for row in connection.execute(
                "SELECT * FROM tags ORDER BY name COLLATE NOCASE, id"
            )]
            assigned = []
            exists = note_id is not None and connection.execute(
                "SELECT 1 FROM notes WHERE id = ?", (note_id,)
            ).fetchone() is not None
            if exists:
                assigned = [row[0] for row in connection.execute(
                    "SELECT tag_id FROM note_tags WHERE note_id = ?", (note_id,)
                )]
            return jsonify(ok=True, tags=tags, assigned=assigned, note_exists=exists)
    except sqlite3.Error:
        app.logger.exception("Tag state failed")
        return tag_error("database", 500)


@app.post("/tags/create")
def create_tag():
    fields = tag_fields()
    if fields is None:
        return tag_error("invalid", 400)
    try:
        with closing(connect_db()) as connection, connection:
            cursor = connection.execute(
                "INSERT INTO tags (name, color, created_at) VALUES (?, ?, ?)",
                (*fields, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
            tag_id = cursor.lastrowid
        return jsonify(ok=True, id=tag_id), 201
    except sqlite3.IntegrityError:
        return tag_error("duplicate", 409)
    except sqlite3.Error:
        app.logger.exception("Create tag failed")
        return tag_error("database", 500)


@app.post("/tags/<int:tag_id>/update")
def update_tag(tag_id):
    if not 1 <= tag_id <= 2**63 - 1:
        return tag_error("not_found", 404)
    fields = tag_fields()
    if fields is None:
        return tag_error("invalid", 400)
    try:
        with closing(connect_db()) as connection, connection:
            cursor = connection.execute(
                "UPDATE tags SET name = ?, color = ? WHERE id = ?", (*fields, tag_id)
            )
            if cursor.rowcount == 0:
                return tag_error("not_found", 404)
        return jsonify(ok=True)
    except sqlite3.IntegrityError:
        return tag_error("duplicate", 409)
    except sqlite3.Error:
        app.logger.exception("Update tag failed")
        return tag_error("database", 500)


@app.post("/tags/<int:tag_id>/delete")
def delete_tag(tag_id):
    if not 1 <= tag_id <= 2**63 - 1:
        return tag_error("not_found", 404)
    try:
        with closing(connect_db()) as connection, connection:
            cursor = connection.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            if cursor.rowcount == 0:
                return tag_error("not_found", 404)
        return jsonify(ok=True)
    except sqlite3.Error:
        app.logger.exception("Delete tag failed")
        return tag_error("database", 500)


@app.post("/notes/<int:note_id>/tags/<int:tag_id>")
def set_note_tag(note_id, tag_id):
    assigned = request.form.get("assigned", type=int)
    if assigned not in (0, 1):
        return tag_error("invalid", 400)
    if not all(1 <= value <= 2**63 - 1 for value in (note_id, tag_id)):
        return tag_error("not_found", 404)
    try:
        with closing(connect_db()) as connection, connection:
            # Serialize the existence checks with the relationship mutation.
            connection.execute("BEGIN IMMEDIATE")
            if (connection.execute("SELECT 1 FROM notes WHERE id = ?", (note_id,)).fetchone() is None
                    or connection.execute("SELECT 1 FROM tags WHERE id = ?", (tag_id,)).fetchone() is None):
                return tag_error("not_found", 404)
            if assigned:
                connection.execute("""
                    INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)
                    ON CONFLICT(note_id, tag_id) DO NOTHING
                """, (note_id, tag_id))
            else:
                connection.execute("DELETE FROM note_tags WHERE note_id = ? AND tag_id = ?", (note_id, tag_id))
        return jsonify(ok=True, assigned=assigned)
    except sqlite3.Error:
        app.logger.exception("Set note tag failed")
        return tag_error("database", 500)


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=3000,
        debug=True
    )
    
import os
import shutil
import sqlite3
from datetime import datetime

import dotenv
from flask import Flask, Response, jsonify, request, send_file, stream_with_context
from send2trash import send2trash
from werkzeug.utils import secure_filename

from tinydist.utils import file_directory, generate_file_stream, get_path_sync

app = Flask(__name__)
dotenv.load_dotenv()


DB_NAME = os.getenv("DATABASE_NAME", "metadata.db")

AUTH_TOKEN = os.getenv("AUTH_TOKEN")


def check_auth(token):
    """Simple check for auth token."""
    return token == AUTH_TOKEN


@app.route("/upload", methods=["POST"])
def upload_file():
    auth_token = request.headers.get("Authorization")
    if not check_auth(auth_token):
        return jsonify({"message": "Unauthorized"}), 401

    file = request.files.get("file")
    category = request.form.get("category", "default")

    if file and file.filename:
        filename = secure_filename(file.filename)
        path = os.path.join(file_directory, filename)
        file.save(path)
        upload_metadata(filename, path, category)
        return jsonify({"message": "File uploaded successfully", "filename": filename})
    return jsonify({"message": "Invalid file format"}), 400


def ensure_directory_exists(path):
    print("path", path)
    if not os.path.isdir(path):
        os.makedirs(path)


def cleanup_failed_upload(filename, chunks_dir_path):
    """
    Deletes all chunks and temporary files associated with a failed upload.
    """
    chunks_path = os.path.join(chunks_dir_path, filename)
    try:
        if os.path.exists(chunks_path):
            shutil.rmtree(chunks_path)
        print(f"Cleanup successful for {filename}")
    except Exception as e:
        print(f"Failed to cleanup {filename}: {e}")


@app.route("/upload_chunk", methods=["POST"])
def upload_chunk():
    auth_token = request.headers.get("Authorization")
    if not check_auth(auth_token):
        return jsonify({"message": "Unauthorized"}), 401

    file = request.files.get("file")
    filename = request.form.get("filename")
    chunk_index = request.form.get("chunkIndex", type=int)
    total_chunks = request.form.get("totalChunks", type=int)
    category = request.form.get("category", "default")
    checksum = request.form.get("checksum")

    filename = os.path.basename(filename)
    chunks_dir_path = os.path.join(file_directory, filename + "_chunks")
    ensure_directory_exists(chunks_dir_path)

    chunk_filename = f"{filename}.part{chunk_index}"
    chunk_path = os.path.join(chunks_dir_path, chunk_filename)
    file.save(chunk_path)
    if chunk_index == total_chunks - 1:
        upload_metadata(filename, chunks_dir_path, category, checksum)

    return jsonify({"message": f"Chunk {chunk_index} uploaded successfully"})


def upload_metadata(filename, path, category, checksum=None):
    """Insert file metadata into the database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS metadata (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename TEXT UNIQUE,
                            path TEXT,
                            checksum TEXT,
                            upload_timestamp DATETIME,
                            last_accessed DATETIME,
                            access_count INTEGER DEFAULT 0,
                            category TEXT)"""
        )
        cursor.execute(
            """INSERT INTO metadata \
                (filename, path, upload_timestamp, category, checksum)
                              VALUES (?, ?, ?, ?, ?)
                              ON CONFLICT(filename) DO UPDATE SET
                              path=excluded.path,
                              upload_timestamp=excluded.upload_timestamp,
                              category=excluded.category,
                              checksum=excluded.checksum""",
            (filename, path, datetime.now(), category, checksum),
        )


@app.route("/metadata", methods=["GET"])
def list_metadata():
    auth_token = request.headers.get("Authorization")
    if not check_auth(auth_token):
        return jsonify({"message": "Unauthorized"}), 401

    limit = request.args.get("limit", 5, type=int)
    category = request.args.get("category", None)

    query = "SELECT * FROM metadata"
    params = []
    if category:
        query += " WHERE category = ?"
        params.append(category)
    query += " ORDER BY upload_timestamp DESC LIMIT ?"
    params.append(limit)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        records = cursor.fetchall()
    return jsonify(records)


@app.route("/verify_get", methods=["POST"])
def verify_upload():
    filename = request.form.get("filename")
    actual_checksum = request.form.get("checksum")
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT checksum FROM metadata WHERE filename = ?", (filename,))
        record = cursor.fetchone()
        print("record", record)
        if not record:
            return jsonify({"message": "File not found"}), 404
        expected_checksum = record[0]
    if actual_checksum == expected_checksum:
        return jsonify({"message": "File is intact"}), 200
    else:
        return jsonify({"message": "File corrupted during transfer"}), 400


@app.route("/get", methods=["GET"])
def get():
    identifier, is_id = (
        (request.args.get("id"), True)
        if request.args.get("id")
        else (request.args.get("filename"), False)
    )
    if not identifier:
        return jsonify({"message": "Missing file identifier"}), 400
    path = get_path_sync(identifier, is_id)

    if not path:
        return jsonify({"message": "File not found"}), 404

    if os.path.isdir(path):
        folder_name = os.path.basename(path).split("_chunks")[0]
        headers = {
            "X-Chunked": "True",
            "Content-Disposition": f'attachment; filename="{folder_name}"',
        }
        return Response(
            stream_with_context(generate_file_stream(path)), headers=headers
        )
    else:
        print("path", path)
        return send_file(path, as_attachment=True)


@app.route("/delete", methods=["DELETE"])
def delete_file_and_or_metadata():
    auth_token = request.headers.get("Authorization")
    if not check_auth(auth_token):
        return jsonify({"message": "Unauthorized"}), 401

    metadata_id = request.args.get("id", type=int)
    filename = request.args.get("filename", type=str)

    if not metadata_id and not filename:
        return jsonify({"message": "Missing metadata ID or filename"}), 400

    message_details = []

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        if metadata_id:
            query = "SELECT filename, path FROM metadata WHERE id = ?"
            params = (metadata_id,)
        elif filename:
            query = "SELECT filename, path FROM metadata WHERE filename = ?"
            params = (filename,)

        cursor.execute(query, params)
        record = cursor.fetchone()

        if record:
            filename, path = record
            if os.path.isdir(path):
                shutil.rmtree(path)
                message_details.append(
                    f"Directory for '{filename}' deleted successfully."
                )
            elif os.path.exists(path):
                send2trash(path)
                message_details.append(f"File '{filename}' deleted successfully.")
            else:
                message_details.append(f"File or directory '{filename}' not found.")
        else:
            message_details.append(
                f"No metadata found for ID {metadata_id} or filename '{filename}'."
            )

        if metadata_id or filename:
            deleted_rows = cursor.execute(
                "DELETE FROM metadata WHERE id = ? OR filename = ?",
                (metadata_id, filename),
            ).rowcount
            if deleted_rows > 0:
                message_details.append("Metadata deleted.")

    return jsonify(
        {
            "message": (
                " ".join(message_details) if message_details else "No action taken."
            )
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")

from flask import Flask, request, jsonify, send_file, after_this_request
import sqlite3
from datetime import datetime
import os
import requests
import dotenv
from werkzeug.utils import secure_filename
import zipfile
import shutil

app = Flask(__name__)
dotenv.load_dotenv()

file_directory = "./files/"
DB_NAME = "metadata.db"

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
        file_path = os.path.join(file_directory, filename)
        file.save(file_path)
        upload_metadata(filename, file_path, category)
        return jsonify({"message": "File uploaded successfully", "filename": filename})
    return jsonify({"message": "Invalid file format"}), 400

def upload_metadata(filename, file_path, category):
    """Insert file metadata into the database."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS metadata (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename TEXT UNIQUE,
                            file_path TEXT,
                            upload_timestamp DATETIME,
                            last_accessed DATETIME,
                            access_count INTEGER DEFAULT 0,
                            category TEXT)""")
        cursor.execute("""INSERT INTO metadata (filename, file_path, upload_timestamp, category)
                          VALUES (?, ?, ?, ?)""",
                       (filename, file_path, datetime.now(), category))

@app.route("/metadata/list", methods=["GET"])
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


@app.route("/files", methods=["GET"])
def get_files():
    auth_token = request.headers.get("Authorization")
    if not check_auth(auth_token):
        return jsonify({"message": "Unauthorized"}), 401

    file_ids = request.args.getlist("id")
    files_to_download = []

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for file_id in file_ids:
            cursor.execute("SELECT file_path FROM metadata WHERE id = ?", (file_id,))
            record = cursor.fetchone()
            if record and os.path.exists(record[0]):
                files_to_download.append(record[0])

    if len(files_to_download) == 1:
        return send_file(files_to_download[0], as_attachment=True)

    elif files_to_download:
        zip_path = os.path.join(file_directory, "files.zip")

        @after_this_request
        def remove_file(response):
            try:
                os.remove(zip_path)
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in files_to_download:
                zipf.write(file, os.path.basename(file))
        return send_file(zip_path, as_attachment=True)

    return jsonify({"message": "No files found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")

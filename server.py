from flask import Flask, request, jsonify, send_file
import sqlite3
from datetime import datetime
import os
import requests
import dotenv

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

    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    file_path = os.path.join(file_directory, file.filename)
    file.save(file_path)
    upload_metadata(file.filename, file_path, "default")
    return jsonify({"message": "File uploaded successfully", "filename": file.filename})

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

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metadata")
        records = cursor.fetchall()
    return jsonify(records)

@app.route("/files", methods=["GET"])
def get_files():
    auth_token = request.headers.get("Authorization")
    if not check_auth(auth_token):
        return jsonify({"message": "Unauthorized"}), 401

    file_ids = request.args.getlist("id")  # Expecting IDs in query string as id=1&id=2
    files = []

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for file_id in file_ids:
            cursor.execute("SELECT file_path FROM metadata WHERE id = ?", (file_id,))
            record = cursor.fetchone()
            if record:
                file_path = record[0]
                if os.path.exists(file_path):
                    files.append(file_path) 
                else:
                    files.append(f"File ID {file_id} not found")
            else:
                files.append(f"Metadata for File ID {file_id} not found")

    return jsonify({"files": files})

if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")

from flask import Flask, request, jsonify, send_file
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)


@app.route("/metadata/upload", methods=["POST"])
def upload_metadata():
    data = request.json
    response = {"status": "error", "message": "Invalid data"}
    if data:
        try:
            with sqlite3.connect("metadata.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS npz_metadata (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    filename TEXT UNIQUE,
                                    file_path TEXT,
                                    upload_timestamp DATETIME,
                                    last_accessed DATETIME,
                                    access_count INTEGER DEFAULT 0,
                                    category TEXT)"""
                )
                cursor.execute(
                    """INSERT INTO npz_metadata (filename, file_path, upload_timestamp, category)
                                  VALUES (?, ?, ?, ?)""",
                    (
                        data["filename"],
                        data["file_path"],
                        datetime.now(),
                        data["category"],
                    ),
                )
                response = {
                    "status": "success",
                    "message": "Metadata uploaded successfully",
                }
        except Exception as e:
            response = {"status": "error", "message": str(e)}
    return jsonify(response)


@app.route("/metadata/list", methods=["GET"])
def list_metadata():
    with sqlite3.connect("metadata.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM npz_metadata")
        records = cursor.fetchall()
    return jsonify(records)


@app.route("/file/<int:file_id>", methods=["GET"])
def stream_file(file_id):
    try:
        with sqlite3.connect("metadata.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_path FROM npz_metadata WHERE id = ?", (file_id,)
            )
            record = cursor.fetchone()
            if record:
                file_path = record[0]
                if os.path.exists(file_path):
                    return send_file(file_path)
                else:
                    return jsonify({"message": "File not found"}), 404
            else:
                return jsonify({"message": "Metadata not found"}), 404
    except Exception as e:
        return jsonify({"message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")

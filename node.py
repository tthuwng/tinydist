from flask import Flask, request, jsonify
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
npz_directory = './npz/'

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and file.filename.endswith('.npz'):
        file_path = os.path.join(npz_directory, file.filename)
        file.save(file_path)
        update_db_with_npz_metadata(file_path)
        return jsonify({"message": "File uploaded successfully", "filename": file.filename})
    else:
        return "Invalid file format", 400

def update_db_with_npz_metadata(file_path, category='default'):
    db_connection = sqlite3.connect('metadata.db')
    cursor = db_connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS npz_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            file_path TEXT,
            upload_timestamp DATETIME,
            last_accessed DATETIME,
            access_count INTEGER DEFAULT 0,
            category TEXT
        )
    ''')
    db_connection.commit()
    db_connection.close()

if __name__ == "__main__":
    app.run(debug=True, port=5001, host='0.0.0.0')

from flask import Flask, jsonify, request, send_file
import sqlite3
import os
import numpy as np
from datetime import datetime

app = Flask(__name__)

@app.route('/process', methods=['GET'])
def process_npz_files():
    top_x = request.args.get('top', default=5, type=int)

    db_connection = sqlite3.connect('metadata.db')
    cursor = db_connection.cursor()

    cursor.execute('''
        SELECT * FROM npz_metadata
        ORDER BY upload_timestamp DESC
        LIMIT ?
    ''', (top_x,))
    records = cursor.fetchall()
    
    processed_files = []
    for record in records:
        file_path = record[2]
        npz_data = np.load(file_path)

        cursor.execute('''
            UPDATE npz_metadata
            SET access_count = access_count + 1, 
                last_accessed = ?
            WHERE id = ?
        ''', (datetime.now(), record[0]))
        db_connection.commit()

        processed_files.append({
            "metadata": {
                "id": record[0],
                "filename": record[1],
                "file_path": record[2],
                "upload_timestamp": record[3],
                "last_accessed": record[4],
                "access_count": record[5],
                "category": record[6]
            },
        })

    db_connection.close()
    return jsonify(processed_files)

@app.route('/list', methods=['GET'])
def list_files_with_data():
    db_connection = sqlite3.connect('metadata.db')
    cursor = db_connection.cursor()

    cursor.execute('SELECT * FROM npz_metadata')
    records = cursor.fetchall()

    files_data = []
    for record in records:
        file_data = {}
        file_data['metadata'] = {
            'id': record[0],
            'filename': record[1],
            'file_path': record[2],
            'upload_timestamp': record[3],
            'last_accessed': record[4],
            'access_count': record[5],
            'category': record[6]
        }

        files_data.append(file_data)

    return jsonify(files_data)

@app.route('/file/<int:file_id>', methods=['GET'])
def stream_file(file_id):
    db_connection = sqlite3.connect('metadata.db')
    cursor = db_connection.cursor()

    cursor.execute('SELECT file_path FROM npz_metadata WHERE id = ?', (file_id,))
    record = cursor.fetchone()
    db_connection.close()

    if record and os.path.exists(record[0]):
        return send_file(record[0])
    else:
        return 'File not found', 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

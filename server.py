from flask import Flask, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route('/process', methods=['GET'])
def process_npz_files():
    db_connection = sqlite3.connect('metadata.db')
    cursor = db_connection.cursor()

    cursor.execute('SELECT * FROM npz_metadata')
    records = cursor.fetchall()
    
    for record in records:
        print(f"Processing {record} for training...")
        cursor.execute('''
            UPDATE npz_metadata
            SET access_count = access_count + 1, 
                last_accessed = ?
            WHERE id = ?
        ''', (datetime.now(), record[0]))
        db_connection.commit()

    db_connection.close()
    return jsonify({"message": "Files processed", "count": len(records)})

@app.route('/files', methods=['GET'])
def list_files():
    db_connection = sqlite3.connect('metadata.db')
    cursor = db_connection.cursor()

    cursor.execute('SELECT * FROM npz_metadata')
    records = cursor.fetchall()

    db_connection.close()
    return jsonify(records)

if __name__ == "__main__":
    app.run(debug=True)
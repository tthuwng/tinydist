import sqlite3
from datetime import datetime

db_connection = sqlite3.connect('metadata.db')
cursor = db_connection.cursor()

def process_npz_files():
    cursor.execute('SELECT * FROM npz_metadata')
    records = cursor.fetchall()
    
    for record in records:
        print(f"Processing {record[1]} for training...")
        print(record)
        cursor.execute('''
            UPDATE npz_metadata
            SET access_count = access_count + 1, 
                last_accessed = ?
            WHERE id = ?
        ''', (datetime.now(), record[0]))
        db_connection.commit()

process_npz_files()

db_connection.close()

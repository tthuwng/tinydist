import os
import sqlite3
from datetime import datetime

npz_directory = './npz/'

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

def update_db_with_npz_metadata(file_path, category='default'):
    filename = os.path.basename(file_path)
    cursor.execute('''
        INSERT INTO npz_metadata (filename, file_path, upload_timestamp, category)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(filename) DO UPDATE SET
        last_accessed=excluded.last_accessed
    ''', (filename, file_path, datetime.now(), category))
    db_connection.commit()

for file in os.listdir(npz_directory):
    if file.endswith('.npz'):
        file_path = os.path.join(npz_directory, file)
        update_db_with_npz_metadata(file_path)

db_connection.close()

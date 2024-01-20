import os
import numpy as np
import sqlite3
from datetime import datetime

npz_directory = './npz/'
if not os.path.exists(npz_directory):
    os.makedirs(npz_directory)

db_connection = sqlite3.connect('metadata.db')
cursor = db_connection.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS npz_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        file_path TEXT,
        upload_timestamp DATETIME,
        last_accessed DATETIME,
        access_count INTEGER DEFAULT 0,
        category TEXT
    )
''')
db_connection.commit()

def save_npz_and_update_db(data, category):
    timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"data_{timestamp_str}.npz"
    file_path = os.path.join(npz_directory, filename)
    
    np.savez(file_path, data)
    
    cursor.execute('''
        INSERT INTO npz_metadata (filename, file_path, upload_timestamp, category)
        VALUES (?, ?, ?, ?)
    ''', (filename, file_path, datetime.now(), category))
    
    db_connection.commit()

data = np.random.rand(10000)  # A long vector
save_npz_and_update_db(data, 'muzero')

db_connection.close()

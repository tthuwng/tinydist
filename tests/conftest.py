import os
import sqlite3

import pytest

from tinydist.server import DB_NAME, app


@pytest.fixture(scope="module")
def client():
    app.config.update(
        {
            "TESTING": True,
        }
    )
    os.makedirs("./files", exist_ok=True)

    create_table_statements = """CREATE TABLE IF NOT EXISTS metadata (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename TEXT UNIQUE,
                            path TEXT,
                            upload_timestamp DATETIME,
                            last_accessed DATETIME,
                            access_count INTEGER DEFAULT 0,
                            category TEXT)"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.executescript(create_table_statements)
        conn.commit()

    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client

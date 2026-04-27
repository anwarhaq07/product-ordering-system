import sqlite3

DB_NAME = "meat.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price_per_kg REAL NOT NULL,
        available INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()
    
import sqlite3
import os
from pathlib import Path

# Get absolute path to project root database
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR/"meat.db"

DB_NAME = "test.db" if os.getenv("TESTING") else "meat.db"

# Create database connection
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)

    # Enable dictionary -like row access
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity_kg REAL NOT NULL,
        status TEXT DEFAULT 'PENDING',
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id) 
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS idempotency_keys(
        key TEXT PRIMARY KEY,
        response TEXT
    )                             
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'customer'
    )
    """)

    conn.commit()
    conn.close()

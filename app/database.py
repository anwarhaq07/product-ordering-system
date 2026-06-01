import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# DB SELECTION (SAFE VERSION)
# -----------------------------
def get_db_name():
    # IMPORTANT: evaluated at runtime, not import time
    #return "test.db" if os.getenv("TESTING") else Path(__file__).resolve().parent/"products.db"
        db = "test.db" if os.getenv("TESTING") else "products.db"
        full_path = BASE_DIR / db
        print("USING DB:", full_path)
        return str(full_path)


# -----------------------------
# DB CONNECTION
# -----------------------------
def get_connection():
    conn = sqlite3.connect(
        get_db_name(),  # FIX: no hardcoded DB
        check_same_thread=False
    )
    # Enables row["column"] access
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    print("DB FILE:", get_db_name())
    return conn


# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # IMPORTANT: USERS FIRST (FK dependency)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'customer'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price_per_kg REAL NOT NULL,
        stock_kg REAL NOT NULL DEFAULT 0,
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
    CREATE TABLE IF NOT EXISTS notification(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_id INTEGER,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        processed INTEGER DEFAULT 0,
        retry_count INTEGER DEFAULT 0,
        last_error TEXT,
        status TEXT DEFAULT "PENDING",
        created_at TIMESTAMP DFAULT CURRENT_TIMESTAMP
    
    )""")

    conn.commit()
    conn.close()
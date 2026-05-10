import sqlite3
import os
import pytest

@pytest.fixture(scope="function")
def client():
    os.environ["TESTING"] = "1"

    # wipe test db
    if os.path.exists("test.db"):
        os.remove("test.db")

    from app.database import init_db
    init_db()

    from app.main import app
    from fastapi.testclient import TestClient

    return TestClient(app)

# -----------------------------
# DB SELECTION (SAFE VERSION)
# -----------------------------
def get_db_name():
    # IMPORTANT: evaluated at runtime, not import time
    return "test.db" if os.getenv("TESTING") else "meat.db"


# -----------------------------
# DB CONNECTION
# -----------------------------
def get_connection():
    conn = sqlite3.connect(
        get_db_name(),  # FIX: no hardcoded DB
        check_same_thread=False
    )
    print("DB FILE:", get_db_name())

    # Enables row["column"] access
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    print("DB FILE:", get_db_name())
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

    # -----------------------------
    # SEED DATA (CRITICAL FOR TESTS)
    # -----------------------------
    cursor.execute("""
    INSERT OR IGNORE INTO products (id, name, price_per_kg, available)
    VALUES (1, 'Lamb', 10.0, 1)
    """)

    conn.commit()
    conn.close()
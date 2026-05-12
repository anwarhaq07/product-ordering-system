import sqlite3
import os
import pytest
from pathlib import Path

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
    return "test.db" if os.getenv("TESTING") else Path(__file__).resolve().parent/"meat.db"


# -----------------------------
# DB CONNECTION
# -----------------------------
def get_connection():
    conn = sqlite3.connect(
        get_db_name(),  # FIX: no hardcoded DB
        check_same_thread=False
    )
    print("DB FILE:", get_db_name())
    print("CWD:", os.getcwd())
    print("DB PATH:", os.path.abspath("meat.db"))

    # Enables row["column"] access
    conn.row_factory = sqlite3.Row
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

    conn.commit()
    conn.close()
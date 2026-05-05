import os
import sqlite3
import pytest
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="function")
def client():

    #Enable test DB
    os.environ["TESTING"] = "1"

    #Reset DB
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS products")

    conn.commit()
    conn.close()

    #Recreate schema

    from app.database import init_db
    init_db()

    return TestClient(app)

import os

#Enable test DB
os.environ["TESTING"] = "1"

import sqlite3
import pytest
from pathlib import Path

from app.database import init_db
init_db()

from app.main import app
from fastapi.testclient import TestClient

TEST_DB = "test.db"

@pytest.fixture(scope="function")
def client():

    #Reset DB
    conn = sqlite3.connect("test.db")
    cursor = conn.cursor()

    # delete DB completely
    if Path(TEST_DB).exists():
        Path(TEST_DB).unlink()

    conn.commit()
    conn.close()

    #Recreate schema



    return TestClient(app)

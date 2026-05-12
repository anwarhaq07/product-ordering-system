import os
#Enable test DB
os.environ["TESTING"] = "1"

import sqlite3
import pytest
from pathlib import Path
TEST_DB = "test.db"

@pytest.fixture(scope="function")
def client():

    # delete DB completely
    if Path(TEST_DB).exists():
        Path(TEST_DB).unlink()

    from app.database import init_db
    init_db()
    
    from seed import seed_db
    seed_db()

    from app.main import app
    from fastapi.testclient import TestClient

    #Recreate schema
    return TestClient(app)
    
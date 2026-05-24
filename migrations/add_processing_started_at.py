import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE events
    ADD COLUMN processing_started_at TIMESTAMP
    """)

conn.commit()
conn.close()

print("Added proocessing_started_at column")
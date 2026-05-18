import json
from app.database import get_connection

def create_event(conn, event_type: str, payload: dict):

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO events (event_type, payload)
        VALUES (?, ?)
        """, (
            event_type,
            json.dumps(payload)
        ))
    
    print("EVENT CREATED:", event_type)
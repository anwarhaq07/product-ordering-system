from app.database import get_connection

def run_migrations():
    
    conn = get_connection()
    cursor = conn.cursor()

    #Check if Column Exists
    cursor.execute("""
        PRAGMA table_info(events)
        """)
    
    columns = [row["name"] for row in cursor.fetchall()]

    if "processing_started_at" not in columns:

        print("Applying migration: processing_started_at")

        cursor.execute("""
            ALTER TABLE events
            ADD COLUMN processing_started_at TIMESTAMP
        """)

        conn.commit()
    conn.close()
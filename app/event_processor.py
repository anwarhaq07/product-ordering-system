import json

from app.database import get_connection
from app.service import create_notification
from app.websocket_manager import manager

async def process_event():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE events
    SET status = 'PENDING'
    WHERE status = 'PROCESSING'
    AND processing_started_at < datetime('now', '-5 minutes')
    """)
    conn.commit()

    cursor.execute("""
        SELECT * FROM events
        WHERE status = "PENDING"
        AND retry_count < 5
        ORDER BY id ASC
        """)
    
    events = cursor.fetchall()

    for event in events:

        try:
            payload = json.loads(event["payload"])
            print("PROCESSING EVENT:", event["event_type"])

            cursor.execute("""
                UPDATE events
                SET status = 'PROCESSING',
                processing_started_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """, (event["id"],))

            conn.commit()
            
            if event["event_type"] == "ORDER_CREATED":
                await manager.send_personal_message(
                    payload["username"],
                    {
                        "event": "ORDER_CREATED",
                        "order_id": payload["order_id"]
                    }
                )

                create_notification(
                    conn = conn,
                    username=payload["username"],
                    event_type = "ORDER_CREATED",
                    event_id = event["id"],
                    message = f"Order #{payload['order_id']} created successfully"
                )
                #raise Exception("CRASH AFTER NOTIFICATION")

                await manager.broadcast_admin({
                    "event": "ORDER_CREATED",
                    "order_id": payload["order_id"],
                    "product": payload["product"],
                    "quantity": payload["quantity"]
                })
            
            cursor.execute("""
                UPDATE events
                SET status = "COMPLETED"
                WHERE id = ?
                """, (event["id"], ))
            conn.commit()
            
            
        except Exception as e:
            print("EVENT FAILED:", event["id"], e)
            new_retry_count =  event["retry_count"] + 1
            status = "DEAD" if new_retry_count >= 5 else "PENDING"

            cursor.execute("""
                UPDATE events
                SET retry_count = ?,
                    last_error = ?,
                    status = ?
                WHERE id = ?
            """, (
                new_retry_count,
                str(e),
                status,
                event["id"]
            ))
            conn.commit()
   
    conn.commit()
    conn.close()


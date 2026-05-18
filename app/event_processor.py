import json

from app.database import get_connection
from app.service import create_notification
from app.websocket_manager import manager

async def process_event():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM events
        WHERE processed = 0
        ORDER BY id ASC
        """)
    
    events = cursor.fetchall()

    for event in events:

        try:
            payload = json.loads(event["payload"])
            print("PROCESSING EVENT:", event["event_type"])

            if event["event_type"] == "ORDER _CREATED":

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
                    message = f"Order #{payload['order_id']} created successfully"
                )

                await manager.broadcast_admin({
                    "event": "ORDER_CREATED",
                    "order_id": payload["order_id"],
                    "product": payload["product"],
                    "quantity": payload["quantity"]
                })
            
            cursor.execute("""
                UPDATE events
                SET processed = 1
                WHERE id = ?
                """, (event["id"], ))
            
        except Exception as e:
            print("EVENT FAILED:", event["id"], e)
   
    conn.commit()
    conn.close()


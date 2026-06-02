from app.database import get_connection
from fastapi import HTTPException
from state_machine import can_transition
import json
from app.auth import hash_password, create_access_token, verify_password
from app.event_service import create_event

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

# Create customer order after validating business rules.
# Update inventory automatically.
def create_order(customer_name, product_id, quantity_kg, username, idempotency_key=None):
    
    # Validate quantity
    if quantity_kg <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # Fetch product
    product = get_product_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code = 404,
            detail = "Product not found"
        )
        
    conn = get_connection()

    try:
        cursor = conn.cursor()

        if idempotency_key:
            cursor.execute("""
            SELECT response FROM idempotency_keys
            WHERE key = ?
            """, (idempotency_key,))
            existing = cursor.fetchone()

            print("IDEMPOTENCY HIT:", existing)
                
            if existing:
                cached = json.loads(existing["response"])
            
            if "order_id" not in cached:
                raise HTTPException(
                status_code=500,
                detail="Corrupted idempotency cache"
                )

            return cached
        
        cursor.execute("""
        SELECT id FROM users
        WHERE username = ?    
        """, (username,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            ) 

        # Transaction starts here
        with conn:

            cursor.execute(
                """
                UPDATE products
                SET stock_kg = stock_kg - ?
                WHERE id = ?
                AND stock_kg >= ?
                """,
                (quantity_kg, product_id, quantity_kg))

            # Reduce Inventory
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock"
                )
         
            # Create order
            cursor.execute(
                """
                INSERT INTO orders
                (customer_name, product_id, quantity_kg, user_id)
                VALUES (?, ?, ?, ?)
                """,
                (customer_name, product_id, quantity_kg, user["id"])
            )
            order_id = cursor.lastrowid
            updated_stock = product["stock_kg"] - quantity_kg
            response_data = {
                "message": "Order created successfully",
                "order_id": order_id,
                "product": product["name"],
                "product_id": product_id,
                "new_stock": updated_stock,
                "quantity": quantity_kg
            }

            create_event(
                conn,
                "ORDER_CREATED",{
                    "username": username,
                    "order_id": response_data["order_id"],
                    "product": product["name"],
                    "quantity": quantity_kg,
                    "product_id": product_id,
                    "new_stock": updated_stock
                }
            )

            if idempotency_key:
                    cursor.execute("""
                    INSERT INTO idempotency_keys (key, response)
                    VALUES (?, ?)
                    """, (idempotency_key, json.dumps(response_data)))

                    print("NEW RESPONSE CACHED:", response_data)

        return response_data

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transaction failed: {str(e)}"
        )
    
    finally:
        conn.close()

# Cancel an order and restore inventory
def cancel_order(order_id, username):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")

        #fetch order and owner
        cursor.execute("""
        SELECT orders.*, users.username
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE orders.id = ?
        """, (order_id, ))

        order = cursor.fetchone()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        #Ownership check
        if order["username"] != username:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to cancel this order"
            )

        cursor.execute("""
            SELECT * FROM orders
            WHERE id = ?
        """, (order_id,))


        #State Validation
        if not can_transition(order["status"], "CANCELLED"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order in {order['status']} state"
            )

        #Restore stocks
        cursor.execute("""
            UPDATE products
            SET stock_kg = stock_kg + ?
            WHERE id = ?
        """, (order["quantity_kg"], order["product_id"]))

        #Mark order cancelled
        cursor.execute("""
            UPDATE orders
            SET status = 'CANCELLED'
            WHERE id = ?
        """, (order_id,))

        #fetch Updated socks
        cursor.execute("""
            SELECT stock_kg
            FROM products
            WHERE id =?
        """, (order["product_id"],))

        product = cursor.fetchone()
        updated_stock = product["stock_kg"]

        cancel_event = {
        "event": "ORDER_CANCELLED",
        "order_id": order_id
        }

        stock_event = {
            "event": "STOCK_UPDATED",
            "product_id": order["product_id"],
            "new_stock": updated_stock
        }

        conn.commit()

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cancellation failed: {str(e)}"
        )

    finally:
        conn.close()
    
    return {
        "message": "Order cancelled successfully",
        "order_id": order_id,
        "product_id": order["product_id"],
        "new_stock": updated_stock
    }

#Fetch product ID
def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    )
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None

#Confirm Order
def confirm_order(order_id):
    conn = get_connection()

    try:
        with conn:
            cursor = conn.cursor()

            #Fetch order
            cursor.execute(
                """
                SELECT * FROM orders
                WHERE id = ?
                """,
                (order_id,)
            )
            order = cursor.fetchone()

            #Validate Orders
            if not order:
                raise HTTPException(
                    status_code=404,
                    detail="Order not found"
                )

            #Validate state transition
            if not can_transition(order['status'], "CONFIRMED"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot confirm order in {order['status']} state"
                )
            
            #Update status
            cursor.execute(
                """
                UPDATE orders
                SET status = 'CONFIRMED'
                WHERE id = ?
                """,
                (order_id,)
            )

        return {
            "message": "Order confirmed successfully"
        }
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"COnfirmation failed:{str(e)}"
        )
    
    finally:
        conn.close()
 
#Mark order as delivered
def deliver_order(order_id):

    conn = get_connection()

    try:
        with conn:

            cursor = conn.cursor()

            #Fetch order
            cursor.execute(
                """
                SELECT * FROM orders
                WHERE id = ?
                """,
                (order_id,)
            )

            order = cursor.fetchone()

            #Validate order
            if not order:
                raise HTTPException(
                    status_code=4-4,
                    detail="Order not found"
                )
            
            #Validate State Transition
            if not can_transition(order["status"], "DELIVERED"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot deliver order in {order['status']} state"
                )
            
            #Update status
            cursor.execute(
                """
                UPDATE orders
                SET status = 'DELIVERED'
                WHERE id = ?
                """,
                (order_id,)
            )

            return{
                "message": "Order delivered successfully"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Delivery Failed: {str(e)}"
        )
    
    finally:
        conn.close()
              
def create_user(username, password, role):

    conn = get_connection()

    try:
        with conn:
            cursor = conn.cursor()

            # Check existing user
            cursor.execute("""
                SELECT id FROM users
                WHERE username = ?
                """, (username,))
            
            existing = cursor.fetchone()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail="Username already exists"
                )
            
            # Hash password
            password_hash = hash_password(password)
            print("CREATING USER:", username, "ROLE:", role)
            # Create User
            cursor.execute("""
                INSERT INTO users(username, password_hash, role)
                VALUES (?, ?, ?)
                """, (username, password_hash, role))
            
            cursor.execute("""
                SELECT username, role
                FROM users
                WHERE username = ?
                """, (username,))

            print("DB USER:", dict(cursor.fetchone()))
            
            return {
                "message": "User created successfully"
            }
        
    finally:
        print("CLOSING CONNECTION", id(conn))
        conn.close()

def login_user(username, password):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE username = ?
        """, (username,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        #Verify Password
        if not verify_password(
            password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        #Generate token
        token = create_access_token({
            "sub": user["username"],
            "role": user["role"]
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }
    finally:
        conn.close()

def create_notification(conn, username, event_type, message, event_id):
    
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id 
    FROM notification
    WHERE event_id = ?
    """, (event_id,))
    existing = cursor.fetchone()

    if existing:
        print("NOTIFICATION ALREADY EXISTS")
        return

    cursor.execute("""
    INSERT INTO notification
    (username, event_type, message, event_id)
    VALUES (?, ?, ?, ?)
    """,(username, event_type, message, event_id))

    conn.commit()



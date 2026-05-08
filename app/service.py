from app.database import get_connection
from fastapi import HTTPException
from state_machine import can_transition
import json
from app.auth import hash_password, create_access_token, verify_password

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
                
            if existing:
                return json.loads(existing["response"])
        
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
            response_data = {
                "message": "Order created successfully",
                "order_id": order_id,
                "product": product["name"]
            }

            if idempotency_key:
                    cursor.execute("""
                    INSERT INTO idempotency_keys (key, response)
                    VALUES (?, ?)
                    """, (idempotency_key, json.dumps(response_data)))

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

        cursor.execute("""
        SELECT orders.*, users.username
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE orders.id = ?
        """, (order_id, ))

        order = cursor.fetchone()

        if order["username"] != username:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to cancel this order"
            )

        cursor.execute("""
            SELECT * FROM orders
            WHERE id = ?
        """, (order_id,))

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if not can_transition(order["status"], "CANCELLED"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order in {order['status']} state"
            )

        cursor.execute("""
            UPDATE products
            SET stock_kg = stock_kg + ?
            WHERE id = ?
        """, (order["quantity_kg"], order["product_id"]))

        cursor.execute("""
            UPDATE orders
            SET status = 'CANCELLED'
            WHERE id = ?
        """, (order_id,))

        conn.commit()

        print("CANCEL SUCCESS:", order["status"])

        return {
            "message": "Order cancelled successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cancellation failed: {str(e)}"
        )

    finally:
        conn.close()

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
              

def create_user(username, password):

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

            # Create User
            cursor.execute("""
                INSERT INTO users(username, password_hash)
                VALUES (?,?)
                """, (username, password_hash))
            
            return {
                "message": "User created successfully"
            }
        
    finally:
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
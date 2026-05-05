from app.database import get_connection
from fastapi import HTTPException
from state_machine import can_transition

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

# Create customer order after validating business rules.
# Update inventory automatically.
def create_order(customer_name, product_id, quantity_kg):
    
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

        # Transaction starts here
        with conn:

            cursor = conn.cursor()

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
                (customer_name, product_id, quantity_kg)
                VALUES (?, ?, ?)
                """,
                (customer_name, product_id, quantity_kg)
            )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transaction failed: {str(e)}"
        )
    
    finally:
        conn.close()

    return {
        "message": "Order created successfully",
        "order_id": cursor.lastrowid,
        "product": product["name"],
        "remaining_stock": product["stock_kg"] - quantity_kg
    }

# Cancel an order and restore inventory
def cancel_order(order_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON")

        cursor.execute("""
            SELECT * FROM orders
            WHERE id = ?
        """, (order_id,))

        order = cursor.fetchone()

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
              


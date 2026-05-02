from app.database import get_connection
from fastapi import HTTPException

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

            # Create order
            cursor.execute(
                """
                INSERT INTO orders
                (customer_name, product_id, quantity_kg)
                VALUES (?, ?, ?)
                """,
                (customer_name, product_id, quantity_kg)
            )

            # Reduce Inventory
            cursor.execute(
                """
                UPDATE products
                SET stock_kg = stock_kg - ?
                WHERE id = ?
                AND stock_kg >= ?
                """,
                (quantity_kg, product_id, quantity_kg)
            )
            
            #rowcount tells how many rows were updated
            if cursor.rowcount == 0:

                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock"
                )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transaction failed: {str(e)}"
        )
    
    finally:
        conn.close()

    return {
        "message": "Order created successfully",
        "product": product["name"],
        "remaining_stock": product["stock_kg"] - quantity_kg
    }

# Cancel an order and restore inventory
def cancel_order(order_id):
    conn = get_connection()

    try:
        with conn:
            cursor = conn.cursor()

            # Fetch Order
            cursor.execute("""
                           SELECT * FROM orders
                           WHERE id = ?
                           """,
                           (order_id,)
                           )
            order = cursor.fetchone()

            # Validate Order
            if not order:
                raise HTTTPException(
                    status_code=404,
                    detail="Order not found"
                )
            
            # Prevent Double Cancellation
            if order["status"] == "CANCELLED":
                raise HTTPException(
                    status_code=400,
                    detail="Order already cancelled"
                )
            
            # Restore inventory
            cursor.execute(
                """
                Update products
                SET stock_kg = stock_kg + ?
                WHERE id = ?
                """,
                (order["quantity_kg"], order["product_id"])
            )

            # Update order status
            cursor.execute(
                """
                UPDATE orders
                SET status = 'CANCELLED'
                WHERE id =?
                """,
                (order_id,)
            )
            return {
                "message" : "Order cancelled successfully"
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
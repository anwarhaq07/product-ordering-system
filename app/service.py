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

    # Validate stock
    if product["stock_kg"] < quantity_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product['stock_kg']}kg available"
        )

    conn = get_connection()
    cursor = conn.cursor()

    # Insert order into database
    cursor.execute(
        """INSERT INTO orders
        (customer_name, product_id, quantity_kg) 
        VALUES (?, ?, ?)
        """,
        (customer_name, product_id, quantity_kg)
    )

    # Reduce stock
    cursor.execute(
        """
        UPDATE products
        SET stock_kg = stock_kg - ?
        WHERE id = ?
        """,
        (quantity_kg, product_id)
    )
    conn.commit()
    conn.close()

    return {
        "message": "Order created successfully",
        "product": product["name"],
        "remaining_stock": product["stock_kg"] - quantity_kg
    }

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
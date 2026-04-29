from app.database import get_connection
from fastapi import HTTPException

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

def create_order(customer_name, product_id, quantity_kg):
    
    product = get_product_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code = 404,
            detail = "Product not found"
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """INSERT INTO orders
        (customer_name, product_id, quantity_kg) 
        VALUES (?, ?, ?)
        """,
        (customer_name, product_id, quantity_kg)
    )
    conn.commit()
    conn.close()

    return {
        "message": "Order created successfully",
        "product": product["name"]
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
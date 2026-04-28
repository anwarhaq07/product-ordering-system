from app.database import get_connection

def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

def create_order(customer_name, product_id, quantity_kg):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO orders(customer_name, product_id, quantity_kg) VALUES (?, ?, ?)",
        (customer_name, product_id, quantity_kg)
    )
    conn.commit()
    conn.close()

    return {"message": "Order created successfully"}
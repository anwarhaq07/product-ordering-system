from app.database import get_connection, init_db

init_db()

def seed_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products
        (name, price_per_kg, stock_kg, available)
        VALUES (?, ?, ?, ?)
        """,
        ("Goat Meat", 10, 1000, 1000)
    )

    cursor.execute(
        """
        INSERT INTO products
        (name, price_per_kg, stock_kg, available)
        VALUES (?, ?, ?, ?)
        """,
        ("Goat Meat", 10, 1000, 1000)
    )
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    for row in rows:
        print(dict(row))

    conn.commit()
    conn.close()
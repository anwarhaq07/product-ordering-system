from app.database import get_connection, init_db

init_db()

conn = get_connection()
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO products (name, price_per_kg, available) VALUES (?,?,?)",
    ("Goat Meat", 10, 1000)
)

cursor.execute(
    "INSERT INTO products (name, price_per_kg, available) VALUES (?, ?, ?)",
    ("Lamb Meat", 10, 500)
)

conn.commit()
conn.close()

print("Seeded data")
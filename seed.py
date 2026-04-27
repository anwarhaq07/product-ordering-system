from app.database import get_connection, init_db

init_db()

conn = get_connection()
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO products (name, price_per_kg, available) VALUES (?,?,?)",
    ("Goat Meat", 12.5, 1)
)

cursor.execute(
    "INSERT INTO products (name, price_per_kg, available) VALUES (?, ?, ?)",
    ("Lamb Meat", 14.0, 1)
)

conn.commit()
conn.close()

print("Seeded data")
import sqlite3

conn = sqlite3.connect("meat.db")
cursor = conn.cursor()

# Add stick_kg column to products table
cursor.execute("""
ALTER TABLE products
ADD COLUMN stock_kg REAL DEFAULT 0
""")

conn.commit()
conn.close()

print("stock_kg column added successfully")
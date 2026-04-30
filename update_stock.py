import sqlite3

conn = sqlite3.connect("meat.db")
cursor = conn.cursor()

# Set initial stock values for products
cursor.execute("""
UPDATE products
SET stock_kg = 10
Where id = 1
""")

cursor.execute("""
UPDATE products
SET stock_kg = 5
WHERE id =2
""")

conn.commit()
conn.close()

print("Stock initialized successfully")

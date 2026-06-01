import sqlite3

conn = sqlite3.connect("products.db")
cursor =conn.cursor()

# Add order status column
cursor.execute("""
               ALTER TABLE orders
               ADD COLUMN status TEXT DEFAULT'PENDING'
               """)

conn.commit()
conn.close()

print("status column added")
from fastapi import APIRouter
from app.database import get_connection

router = APIRouter()

@router.get("/")
def home():
    return {"status" : "backend runnning"}

@router.get("/products")
def get_products():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]
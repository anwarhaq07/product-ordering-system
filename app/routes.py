from fastapi import APIRouter
from app.database import get_connection
from app.service import get_all_products, create_order, cancel_order
from pydantic import BaseModel

router = APIRouter()

@router.get("/")
def home():
    return {"status" : "backend runnning"}

@router.get("/products")
def get_products():
    return get_all_products()

class OrderRequest(BaseModel):
    customer_name: str
    product_id: int
    quantity_kg: float

@router.post("/orders")
def create_order_api(order: OrderRequest):
    return create_order(
        order.customer_name,
        order.product_id,
        order.quantity_kg
    )

@router.get("/orders")
def get_orders():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

@router.post("/orders/{order_id}/cancel")
def cancel_order_api(order_id: int):
    return cancel_order(order_id)
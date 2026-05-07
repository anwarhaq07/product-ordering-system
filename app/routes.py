from fastapi import APIRouter, Header
from app.database import get_connection
from app.service import get_all_products, create_order, cancel_order, confirm_order, deliver_order, create_user,login_user
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
def create_order_api(order: OrderRequest,
                     idempotency_key: str | None = Header(default=None)):
    
    return create_order(
        order.customer_name,
        order.product_id,
        order.quantity_kg,
        idempotency_key=idempotency_key
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

@router.post("/prders/{order_id}/conifrm")
def confirm_order_api(order_id: int):
    return confirm_order(order_id)

@router.post("/orders/{order_id}/deliver")
def deliver_order_api(order_id: int):
    return deliver_order(order_id)


class UserRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register_user(user: UserRequest):

    return create_user(
        user.username,
        user.password
    )

class LoginRequest(BaseModel):
    username : str
    password: str

@router.post("/login")
def login_api(user: LoginRequest):
    return login_user(
        user.username,
        user.password
    )
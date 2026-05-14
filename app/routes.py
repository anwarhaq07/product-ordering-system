from fastapi import APIRouter, Header, Depends
from app.websocket_manager import manager
from app.database import get_connection
from app.service import get_all_products, create_order, cancel_order, confirm_order, deliver_order, create_user,login_user
from pydantic import BaseModel
from app.auth import get_current_user,require_admin
from fastapi.security import OAuth2PasswordRequestForm

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
async def create_order_api(
    order: OrderRequest,
    current_user: dict = Depends(get_current_user),
    idempotency_key: str | None = Header(default=None)):
    
    result = create_order(
        order.customer_name,
        order.product_id,
        order.quantity_kg,
        idempotency_key=idempotency_key,
        username=current_user["username"]
    )
    print("DEBUG RESPONSE FROM SERVICE:", result)
    print("********************ABOUT TO BROADCAST*******************")
    print("ROUTE MANAGER:", id(manager))

    await manager.send_personal_message(
        current_user["username"],
        {
        "event": "ORDER CREATED",
        "order_id": result["order_id"],
        "product": result["product"],
        "quantity": result["quantity"]
    })

    await manager.broadcast({
        "event": "STOCK_UPDATED",
        "product_id": result["product_id"],
        "new_stock": result["new_stock"]
    })
    return result

@router.get("/orders")
def get_orders():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

@router.post("/orders/{order_id}/cancel")
async def cancel_order_api(order_id: int, current_user: dict = Depends(get_current_user)):

    result = cancel_order(order_id, current_user["username"])

    await manager.send_personal_message(
        current_user["username"],
        {
        "event": "ORDER CANCELLED",
        "order_id": result["order_id"]
    })

    await manager.broadcast({
        "event": "STOCK_UPDATED",
        "product": result["product_id"],
        "new_stock": result["new_stock"]
    })

    return result

@router.post("/orders/{order_id}/confirm")
def confirm_order_api(order_id: int, current_user: dict = Depends(get_current_user)):
    
    require_admin(current_user)
    return confirm_order(order_id)

@router.post("/orders/{order_id}/deliver")
def deliver_order_api(order_id: int, current_user: dict = Depends(get_current_user)):
    require_admin(current_user)
    return deliver_order(order_id)


class UserRequest(BaseModel):
    username: str
    password: str
    role: str = "customer"

@router.post("/register")
def register_user(user: UserRequest):

    return create_user(
        user.username,
        user.password,
        user.role
    )

class LoginRequest(BaseModel):
    username : str
    password: str

@router.post("/login")
def login_api(form_data: OAuth2PasswordRequestForm = Depends()):
    return login_user(  
        form_data.username,
        form_data.password
    )

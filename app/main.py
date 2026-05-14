from fastapi import FastAPI,WebSocket
from app.routes import router
from app.database import init_db
from app.websocket_manager import manager
from seed import seed_db

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()
    seed_db()

@app.websocket("/ws/orders/{username}")
async def order_ws(websocket: WebSocket, username:str):
    await manager.connect(username, websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect_customer(websocket)


@app.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket):

    await manager.connect_admin(websocket)

    try:
        while True:
            await websocket.receive_text()
    
    except:
        manager.disconnect_admin(websocket)

app.include_router(router)
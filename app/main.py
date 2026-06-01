from fastapi import FastAPI,WebSocket
from app.routes import router
from app.database import init_db
from app.websocket_manager import manager
from seed import seed_db
from starlette.websockets import WebSocketDisconnect
import asyncio
from contextlib import asynccontextmanager
from app.event_processor import process_event
from app.migrations import run_migrations
asynccontextmanager
async def lifespan(app: FastAPI):

    print("STARTING APPLICATION")

    init_db()
    run_migrations()
    seed_db()

    yield

    print("SHUTING DOWN APPLICATION")

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/orders/{username}")
async def order_ws(websocket: WebSocket, username:str):
    await manager.connect(username, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print("CLIENT MESSAGE:", data)
    except WebSocketDisconnect:
        print("DISCONNECTED:", username)
        manager.disconnect_customer(username, websocket)
    
    except Exception as e:
        print("WS ERROR:", e)
        manager.disconnect_customer(username, websocket)


@app.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket):

    await manager.connect_admin(websocket)

    try:
        while True:
            await websocket.receive_text()
    
    except:
        manager.disconnect_admin(websocket)

app.include_router(router)

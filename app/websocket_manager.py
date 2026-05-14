from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.admin_connections = []

    async def connect(self, username: str, websocket: WebSocket):
        
        await websocket.accept()
        self.active_connections[username] = websocket
        print(f"{username} CONNECTED")

    async def connect_admin(
            self,
            websocket: WebSocket
    ):
        await websocket.accept()
        self.admin_connections.append(websocket)
        print("ADMIN CONNECTED")

    def disconnect_customer(self, username: str):
        
        if username in self.active_connections:
            del self.active_connections[username
                                        ]
        print("DISCONNECTED")

    def disconnect_admin(self, websocket:WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def send_personal_message(self, username:str, message: dict):

        websocket = self.active_connections.get(username)

        if websocket:
            await websocket.send_json(message)

    async def broadcast_admin(self, message:dict):
        for admin_ws in self.admin_connections:
            await admin_ws.send_json(message)

manager = ConnectionManager()
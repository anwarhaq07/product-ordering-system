from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
        self.admin_connections = []

    async def connect(self, username: str, websocket: WebSocket):
        
        await websocket.accept()

        if username not in self.active_connections:
            self.active_connections[username] = []
        
        self.active_connections[username].append(websocket)
        print(f"{username} CONNECTED")

    async def connect_admin(
            self,
            websocket: WebSocket
    ):
        await websocket.accept()
        self.admin_connections.append(websocket)
        print("ADMIN CONNECTED")

    def disconnect_customer(self, username: str, websocket: WebSocket):
        
        connection = self.active_connections.get(username)

        if not connection:
            return
        
        if websocket in connection:
            connection.remove(websocket)
        
        if len(connection) == 0:
            del self.active_connections[username]
        
        print("DISCONNECTED")

    def disconnect_admin(self, websocket:WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def send_personal_message(self, username:str, message: dict):

        connections = self.active_connections.get(username, [])

        for websocket in connections:
            try:
                await websocket.send_json(message)
            
            except Exception:
                pass

    async def broadcast_admin(self, message:dict):
        disconnected = []
        
        for admin_ws in self.admin_connections:
            try:
                await admin_ws.send_json(message)
            except Exception:
                disconnected.append(admin_ws)
        
        for dead_ws in disconnected:
            self.admin_connections.remove(dead_ws)
            print("Removed dead admin connection")

manager = ConnectionManager()
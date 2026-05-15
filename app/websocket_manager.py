from fastapi import WebSocket
import asyncio

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
            print("NO ACTIVE CONNECTION FOR:", username)
            return
        try:
            if websocket in connection:
                connection.remove(websocket)
            if not connection:
                del self.active_connections[username]
                print("DISCONNECTED:", username)
        
        except Exception as e:
            print("DISCONNECT ERROR:", e)
        

    def disconnect_admin(self, websocket:WebSocket):
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def send_personal_message(self, username:str, message: dict):

        tasks = []
        connections = self.active_connections.get(username, [])
        for connection in connections:
            tasks.append(
                connection.send_json(message)
            )
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        dead_connections = []

        for connection, result in zip(connections, results):
            if isinstance(result, Exception):
                dead_connections.append(connection)
        for dead_ws in dead_connections:
            connections.remove(dead_ws)
            print("Remove dead customer connection")

    async def broadcast_admin(self, message:dict):
        tasks = []
        connections = list(self.admin_connections)
        
        for connection in connections:
            
            tasks.append(
                connection.send_json(message)
            )
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        for connection, result in zip(connections, results):
            if isinstance(result, Exception):
                self.admin_connections.remove(self.connection)

                print("REMOVED DEAD ADMIN CONNECTION")

manager = ConnectionManager()
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket

        print(f"{username} CONNECTED")
        print("TOTAL CONNECTIONS:", len(self.active_connections))
        print("CONNECT MANAGER:", id(self))

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username
                                        ]
        print("DISCONNECTED")
        print("TOTAL CONNECTIONS:", len(self.active_connections))

    async def send_personal_message(self, username:str, message: dict):

        websocket = self.active_connections.get(username)

        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, message:dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()
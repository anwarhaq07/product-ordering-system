from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        print("CONNECTED")
        print("TOTAL CONNECTIONS:", len(self.active_connections))
        print("CONNECT MANAGER:", id(self))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

        print("DISCONNECTED")
        print("TOTAL CONNECTIONS:", len(self.active_connections))

    async def broadcast(self, message:dict):
        for connection in self.active_connections:
            await connection.send_json(message)

            print("********************INSIDE BROADCAST******************")
            print("BROADCASTING:", message)
            print("ACTIVE CONNECTIONS:", len(self.active_connections))
            print("BROADCAST MANAGER:", id(self))

            for connection in self.active_connections:
                print("SENDING MESSAGE")
                await connection.send_json(message)
manager = ConnectionManager()
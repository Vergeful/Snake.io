import asyncio
import websockets
from .shared_state import SERVERS, THIS_SERVER

class ReplicaConnectionManager:
    def __init__(self):
        self.connections = {}           # { "replica_host:port": websocket connection }
        self.initialized = False        # Initially, primary is not connected to backups
        self.lock = asyncio.Lock()

    # Allow connection to replicas to only run on 1st connection to PlayerConsumer:          
    async def initialize_connections(self):
        async with self.lock:
            if self.initialized:
                return
            for server in SERVERS:
                if server != THIS_SERVER:
                    asyncio.create_task(self.connect(server))
            self.initialized = True

    async def connect(self, server):
        while True:
            try:
                ws = await websockets.connect(f'ws://{server}/ws/propagated_data')
                self.connections[server] = ws
                print(f"Primary connected to replica: {server}")
                await self.listen(ws)  # Keep connection alive
            except Exception as e:
                print(f"Primary failed to connect to: {server}")
                print(f" Error: {e}")

            await asyncio.sleep(5)  # Retry with delay

    # Keeps the connection open:
    async def listen(self, ws):
        try:
            while True:
                await asyncio.sleep(30)
        except websockets.ConnectionClosed:
            print("A replica has been disconnected.")

    async def send(self, server, message):
        ws = self.connections.get(server)
        if ws:
            try:
                await ws.send(message)
            except Exception as e:
                print(f"Failed to send to {server}: {e}")


# Instantiate the shared replica connection manager:
REPLICA_MANAGER = ReplicaConnectionManager()

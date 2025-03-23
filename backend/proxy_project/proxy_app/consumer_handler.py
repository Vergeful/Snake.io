import json
import asyncio
import websockets
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

SERVERS = ['ws://localhost:8001', 'http://localhost:8002', 'http://localhost:8003']
PRIMARY_SERVER = SERVERS[0]

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # now we need to establish a websocket connection to the primary server
        print("We're connected now")
        self.player_id = self.scope['url_route']['kwargs']['player_id']

        await self.accept()

        self.replica_socket = await websockets.connect(PRIMARY_SERVER + "/ws/game/" + self.player_id)

        asyncio.create_task(self.listen_to_server())

    async def disconnect(self, close_code):
        if self.replica_socket:
            await self.replica_socket.close()
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Forward the WebSocket message to the primary replica
        #response = await self.send_to_primary(text_data_json)
        #await self.send(text_data=json.dumps(response))

        await self.replica_socket.send(text_data_json)

    async def listen_to_server(self):
        try:
            async for message in self.replica_socket:
                # Forward message to frontend
                await self.send(message)
        except websockets.exceptions.ConnectionClosed:
            print("The Server's Dead")
        pass

    async def send_to_primary(self, text_data_json):
        global PRIMARY_SERVER
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f'{PRIMARY_SERVER}/ws/game/') as ws:
                    await ws.send_json(text_data_json)
                    response = await ws.receive()
                    return json.loads(response.data)
        except Exception as e:
            print(f"Primary replica could not be reached: {PRIMARY_SERVER}")
            # If the primary replica fails, we attempt to find a new one
            for server in SERVERS:
                if server != PRIMARY_SERVER:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.ws_connect(f'{server}/game/') as ws:
                                await ws.send_json(text_data_json)
                                response = await ws.receive()
                                PRIMARY_SERVER = server  # Update the primary server
                                return json.loads(response.data)
                    except Exception as e:
                        print(f"Backup replica could not be reached: {server}")
                        continue
            return {'error': 'All replica servers could not be reached.'}
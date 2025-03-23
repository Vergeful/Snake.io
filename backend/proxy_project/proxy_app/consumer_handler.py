import json
import asyncio
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

SERVERS = ['http://localhost:8001', 'http://localhost:8002', 'http://localhost:8003']
PRIMARY_SERVER = SERVERS[0]

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Forward the WebSocket message to the primary replica
        response = await self.send_to_primary(text_data_json)
        await self.send(text_data=json.dumps(response))

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
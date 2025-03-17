import json
import asyncio
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

SERVERS = ['http://localhost:8000', 'http://localhost:8001', 'http://localhost:8002']
PRIMARY_SERVER = SERVERS[0]

class ProxyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Send message to primary replica
        response = await self.send_to_primary(text_data_json)
        await self.send(text_data=json.dumps(response))

    async def send_to_primary(text_data_json):
        global PRIMARY_SERVER
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f'{PRIMARY_SERVER}/ws/game/') as ws:
                    await ws.send_json(text_data_json)
                    response = await ws.receive()
                    return json.loads(response.data)
        except Exception as e:
            print(f"Primary replica failed: {PRIMARY_SERVER}")
            # Switch to another replica if the primary fails
            for server in SERVERS:
                if server != PRIMARY_SERVER:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.ws_connect(f'{server}/ws/game/') as ws:
                                await ws.send_json(text_data_json)
                                response = await ws.receive()
                                PRIMARY_SERVER = server
                                return json.loads(response.data)
                    except Exception as e:
                        print(f"Replica {server} failed: {e}")
                        continue
            return {'error': 'No replica could be reached.'}
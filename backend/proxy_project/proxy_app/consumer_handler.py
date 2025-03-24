import json
import websockets
import aiohttp
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

SERVERS = ['ws://localhost:8001/ws/game/', 'ws://localhost:8002/ws/game/', 'ws://localhost:8003/ws/game/']

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.primary_server = None
        self.primary_connection = None

        # Get player_id from url to access websocket with primary replica:
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]

        await self.connect_to_primary()

    # When the client establishes a websocket connection with the proxy, try to establish connection with primary:
    async def connect_to_primary(self):
        for server in SERVERS:
            try:
                self.primary_connection = await websockets.connect(f'{server}{self.player_id}')
                self.primary_server = server
                print(f'Primary server: {server}')
                return
            except Exception as e:
                print(f'Server could not be reached: {server}')
            
        print("All servers are down.")
        await self.close()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Try to send data from client to primary replica:
        try:
            if not self.primary_connection:
                self.trigger_leader_election()
            
            # Set a timeout for the primary server response:
            response = await asyncio.wait_for(self.send_to_primary(text_data), timeout=1)

            # Send the response back to the client:
            await self.send(response) 

        except asyncio.TimeoutError:
             print("Primary server timeout of 1 second. Triggering leader election...")
             await self.trigger_leader_election()

            # Send intial data from client to newly elected leader:
             response = await self.send_to_primary(text_data)
             await self.send(response) 
             
        
        except Exception as e:
            print(f"Primary server error: {e}")
            print(f"Triggering leader election...")
            await self.trigger_leader_election()

            # Send intial data from client to newly elected leader:
            response = await self.send_to_primary(text_data)
            await self.send(response) 

    # Send data from client to primary replica over websocket connection
    async def send_to_primary(self, text_data):
        await self.primary_connection.send(text_data)
        return await self.primary_connection.recv()
    
    async def trigger_leader_election(self):
        print(f"Leader election begins ...")
        pass


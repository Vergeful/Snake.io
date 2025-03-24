import json
import websockets
import aiohttp
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .shared_state import SERVERS, PRIORITY, get_primary, update_primary

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
        # Check if primary server is up:
        primary_shared = get_primary()
        try:
            self.primary_connection = await websockets.connect(f'ws://{primary_shared}/ws/game/{self.player_id}')
            self.primary_server = 'ws://{primary_shared}/ws/game/{self.player_id}'
            print(f'Primary server: {primary_shared}')
            asyncio.create_task(self.listen_to_server())
            return
        except Exception as e:
            print(f'Primary replica could not be reached.')
            await self.trigger_leader_election() 

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Try to send data from client to primary replica:
        try:            
            # Set a timeout for the primary server response:
            await self.primary_connection.send(text_data)

            # Send the response back to the client:
            # await self.send(response)            
        
        except Exception as e:
            print(f"Primary server error: {e}")
            print(f"Triggering leader election...")
            await self.trigger_leader_election()

            # Send intial data from client to newly elected leader:
            response = await self.primary_connection.send(text_data)
            await self.send(response) 
    
    async def listen_to_server(self):
        try:
            async for message in self.primary_connection:
                # Forward message to frontend
                try:
                    await self.send(message)
                except Exception:
                    print("Something Went Wrong")
                    self.trigger_leader_election()
                    break
        except websockets.exceptions.ConnectionClosed:
            # now we have to trigger leader election
            self.trigger_leader_election()
            pass

    # Send data from client to primary replica over websocket connection
    async def send_to_primary(self, text_data):
        await self.primary_connection.send(text_data)
    
    async def trigger_leader_election(self):
        print(f"Leader election begins ...")
        pass


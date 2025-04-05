import json
import websockets
import aiohttp
import asyncio
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from .shared_state import SERVERS, PRIORITY, get_primary, update_primary
from rest_framework import status
from .leader_functions import check_alive_servers, notify_replicas
from rest_framework.response import Response

# Logical clock at the proxy starts at 0:
LAMPORT_CLOCK = 0

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
        global LAMPORT_CLOCK

        # Check if primary server is up:
        primary_shared = get_primary()
        try:
            self.primary_connection = await websockets.connect(f'ws://{primary_shared}/ws/game/{self.player_id}')
            self.primary_server = 'ws://{primary_shared}/ws/game/{self.player_id}'
            print(f'Primary server: {primary_shared}')

            # Request Lamport clock synchronization from primary server when it connects:
            await self.primary_connection.send(json.dumps({"type": "get_lamport_clock"}))
            # Wait for the response to sync clocks:
            response = await self.primary_connection.recv()
            primary_clock = json.loads(response).get("lamport_clock", LAMPORT_CLOCK)
            self.lamport_clock = max(self.lamport_clock, primary_clock)


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
            response = await self.send_to_primary(text_data)
            
            # Send the response back to the client:
            await self.send(response)            
        
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
            pass

    # Send data from client to primary replica over websocket connection
    async def send_to_primary(self, text_data):
        global LAMPORT_CLOCK

        # Increment clock for incoming data to ensure consistent writes at the primary server:
        LAMPORT_CLOCK += 1
        data = json.loads(text_data)
        data["timestamp"] = LAMPORT_CLOCK

        response = await self.primary_connection.send(json.dumps(data))
        return response
    
    async def trigger_leader_election(self):
        print("Leader election started...")
        print("But inside the consumer this time")

        alive_servers = check_alive_servers()

        if not alive_servers:
            return Response(
                {"error": "Primary and all backup replicas are unavailable."},
                status = status.HTTP_400_BAD_REQUEST
            )
        
        # Sort array so that servers with lower indices are lowest in the SERVERS array.
        # These servers at lower indices have higher priorities.
        sorted_alive_servers = sorted(alive_servers, key=lambda x: x[0])

        # Get replica with highest priority that responded:
        new_primary_server_index , new_primary_server = sorted_alive_servers[0]
        print(f'New primary server: {new_primary_server}')
        update_primary(new_primary_server)
        notify_replicas(new_primary_server_index)
        await self.connect_to_primary()
        pass
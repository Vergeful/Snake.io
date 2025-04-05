import json
import websockets
import asyncio
from asyncio import Queue  # Use asyncio.Queue for async FIFO queue
from channels.generic.websocket import AsyncWebsocketConsumer
from .shared_state import get_primary, update_primary
from .leader_functions import check_alive_servers, notify_replicas
from rest_framework import status
from rest_framework.response import Response

class GameConsumer(AsyncWebsocketConsumer):
    def __init__(self):
        super().__init__()
        self.logical_clock = 0  # Initialize logical clock
        self.message_queue = Queue()  # Use asyncio.Queue for async FIFO queue

    async def connect(self):
        await self.accept()
        self.primary_server = None
        self.primary_connection = None
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        await self.connect_to_primary()

    async def connect_to_primary(self):
        primary_shared = get_primary()
        try:
            self.primary_connection = await websockets.connect(f'ws://{primary_shared}/ws/game/{self.player_id}')
            self.primary_server = f'ws://{primary_shared}/ws/game/{self.player_id}'
            print(f'Primary server: {primary_shared}')
            asyncio.create_task(self.listen_to_server())
        except Exception as e:
            print(f'Primary replica could not be reached.')
            await self.trigger_leader_election()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)

            
            self.logical_clock += 1  # Increment the logical clock

            # Add the timestamp to the message data
            data["timestamp"] = self.logical_clock

            # Enqueue the message in the FIFO queue (async)
            await self.message_queue.put(data)

            # Send the message to the primary server
            await self.process_queue()

        except Exception as e:
            print(f"Error in receive: {e}")
            print(f"Triggering leader election...")
            await self.trigger_leader_election()

    async def process_queue(self):
        # Process messages in FIFO order based on their Lamport timestamp
        latest_message = None
        
        # Retrieve and clear all messages in the queue, getting the latest one based on timestamp
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            if latest_message is None or message["timestamp"] > latest_message["timestamp"]:
                latest_message = message
        
        # If a latest message exists, process and send it
        if latest_message:
            await self.primary_connection.send(json.dumps(latest_message))

    async def listen_to_server(self):
        try:
            async for message in self.primary_connection:
                try:
                    await self.send(message)
                except Exception:
                    print("Something went wrong while forwarding message to client")
                    await self.trigger_leader_election()
                    break
        except websockets.exceptions.ConnectionClosed:
            await self.trigger_leader_election()

    async def send_to_primary(self, text_data):
        await self.primary_connection.send(text_data)

    async def trigger_leader_election(self):
        print("Leader election started... (inside consumer)")

        alive_servers = check_alive_servers()

        if not alive_servers:
            return Response(
                {"error": "Primary and all backup replicas are unavailable."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sorted_alive_servers = sorted(alive_servers, key=lambda x: x[0])
        new_primary_server_index, new_primary_server = sorted_alive_servers[0]
        print(f'New primary server: {new_primary_server}')
        update_primary(new_primary_server)
        notify_replicas(new_primary_server_index)
        await self.connect_to_primary()

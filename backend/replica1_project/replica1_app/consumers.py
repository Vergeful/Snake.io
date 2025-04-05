import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Player
import random
import asyncio
import requests
from .shared_state import SERVERS, THIS_SERVER, get_primary, update_primary_server, PRIORITY
from collections import deque
from heapq import heappush, heappop
import websockets

# SERVERS = ['ws://localhost:8001/ws/game/', 'ws://localhost:8002/ws/game/', 'ws://localhost:8003/ws/game/']

"""Functions for accesssing database through websockets"""
@database_sync_to_async
def get_player(player_id):
    from .models import Player
    return Player.objects.get(id=player_id)

@database_sync_to_async
def save_player(player):
    from .models import Player
    player.save()


"""Constants for world and server configuration"""
TICK_RATE = 60
WORLD_BOUNDS = {
    "x_min": 0,
    "x_max": 1000,
    "y_min": 0,
    "y_max": 1000
}
FOOD_COUNT = 20
FOOD_LIST = [] 
PLAYERS = {}

# Lamport clock and priority queue:
LAMPORT_CLOCK = 0
EVENT_QUEUE = deque()

# Send created food list to replicas on initial connection:
async def propagate_food_list_to_replicas(food_data):
    global SERVERS
    global THIS_SERVER
    for server in SERVERS:
        if server != THIS_SERVER:
            try:
                # This endpoint has not been created yet:
                response = requests.post(f"http://{server}/replica/update_food_list/", json=food_data)
                if response.status_code == 200:
                    print(f"Successfully sent food list to {server}")
                else:
                    print(f"Failed to send food list to {server}")
            except:
                print(f"Server did not respond: {server}")

# Send message to replicas over websocket:
async def propagate_event_to_replicas(event_data):
    global SERVERS
    global THIS_SERVER
    # Send WebSocket messages to all replica servers
    for server in SERVERS:
        if server != THIS_SERVER:
            try:
                # This websocket class has not been created fully, see below:
                async with websockets.connect(f'ws://{server}/ws/propagated_data') as websocket:
                    await websocket.send(json.dumps(event_data))
                    print(f"Successfully sent event to {server}")
            except Exception as e:
                print(f"Server did not respond: {server}")

def generate_food():
    """
    Creates random food positions in the world
    """
    global FOOD_LIST
    FOOD_LIST = [
        {"id": i, "x": random.randint(WORLD_BOUNDS["x_min"], WORLD_BOUNDS["x_max"]),
         "y": random.randint(WORLD_BOUNDS["y_min"], WORLD_BOUNDS["y_max"])}
        for i in range(FOOD_COUNT)
    ]

class PlayerConsumer(AsyncWebsocketConsumer):
    
    # Keeps track of all the player data in the server
    """
    Keeps track of all the player data in the server

    json structure
    player_id: string : {
        "x": number
        "y": number
        "size": number
        "speed": number
        "score": number
        "color": string
    }
    """
    async def connect(self):
        global FOOD_LIST
        global PLAYERS
        """
        Handles connection of websocket from frontend
        """

        # Adding players to group:
        self.room_name= "game_room"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # Start the game loop (for server tick rate):
        self.game_loop_task = asyncio.create_task(self.game_loop())

        # Generating a food list in none is initialized:
        if not FOOD_LIST:
            generate_food()
            # Notify replicas of new food list:
            await propagate_food_list_to_replicas(FOOD_LIST)

        # Get player id from url:
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        player = await get_player(self.player_id)

        # Initializing the player configuration
        PLAYERS[self.player_id] = {
            "x": 400,  
            "y": 300,
            "size": 40,
            "speed": 150,
            "score": player.score,
            "color": player.color,  
        }

        # Sends connecting websocket the pre-existing players
        await self.send(json.dumps({
            "type": "all_players", 
            "players": PLAYERS,
            "food": FOOD_LIST
            }))

        # Broadcast to other socket in group of joined player
        await self.broadcast({
            "type": "player_joined",
            "id": self.player_id,
            "x": PLAYERS[self.player_id]["x"],
            "y": PLAYERS[self.player_id]["y"],
            "speed": PLAYERS[self.player_id]["speed"],
            "size": PLAYERS[self.player_id]["size"],
            "color": PLAYERS[self.player_id]["color"],
        })


    async def disconnect(self, close_code):
        global PLAYERS
        """
        Handles disconnected websocket
        """
        if self.player_id in PLAYERS:
            del PLAYERS[self.player_id]
            await self.broadcast({"type": "player_left", "id": self.player_id})

    
    def check_collision(self, player, food):
        """
        Check if a player collides with a food piece
        """
        return (player["x"] - food["x"])**2 + (player["y"] - food["y"])**2 <= player["size"]**2


    async def receive(self, text_data):     
        global LAMPORT_CLOCK

        """
        Receive a message from the WebSocket
        """
        # If the player does not exist:
        try:
            player = await get_player(self.player_id)
        except player.DoesNotExist:
            await self.send(json.dumps({"error": "Player not found"}))
            return
        
        data = json.loads(text_data)
        timestamp = data.get("timestamp")
        # Ignore events without a timestamp:
        if timestamp is None:
            return  
        
        # Update local lamport clock:
        LAMPORT_CLOCK = max(LAMPORT_CLOCK, timestamp) + 1

        # If event's timestamp is newer, add it to the queue:
        if timestamp >= LAMPORT_CLOCK:
            heappush(EVENT_QUEUE, (timestamp, data))
        else:
            print(f"Discarded event with out-of-order timestamp: {timestamp}")


    async def process_event(self, data):
        global PLAYERS

        if data["type"] == "move":
            pid = str(data["id"])

            if pid not in PLAYERS:
                return

            intended_x = data["x"]
            intended_y = data["y"]

            new_x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], intended_x))
            new_y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], intended_y))

            PLAYERS[str(data["id"])]["x"] = new_x
            PLAYERS[str(data["id"])]["y"] = new_y


    async def game_loop(self):
        global EVENT_QUEUE
        global PLAYERS

        """
        Game tick loop
        """
        try:
            while True:
                await asyncio.sleep(1/ TICK_RATE)

                # Process events in the order of timestamps:
                event = None
                if EVENT_QUEUE:
                    _, event = heappop(EVENT_QUEUE)
                    await self.process_event(event)                        

                # Send event to backup replicas:
                if event:
                    await propagate_event_to_replicas(event)

                await self.broadcast({
                    "type": "update",
                    "id": self.player_id,
                    "x": PLAYERS[self.player_id]["x"],
                    "y": PLAYERS[self.player_id]["y"]
                })

        except asyncio.CancelledError:
            pass
    
    async def broadcast(self, message):
        """Send message to all connected players in the group"""
        await self.channel_layer.group_send(
            "game_room",
            {
                "type": "send_message",
                "message": json.dumps(message),
            }
        )
    
    async def send_message(self, event):
        """Send the broadcast message to each connected WebSocket"""
        await self.send(text_data=event["message"])


class ReplicaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Replica connected to Primary Server.")
        await self.accept()
 
    async def disconnect(self, close_code):
        global THIS_SERVER
        print(f'Replica disconnected from Primary Server: {THIS_SERVER}')
 
    async def receive(self, text_data):
        global LAMPORT_CLOCK

        try:
            event = json.loads(text_data)
            
            # Check if the event's timestamp is newer than our Lamport clock
            timestamp = event.get('timestamp', None)
            if timestamp is None:
                print("Event has no timestamp so we discard it.")
                return
           
           # If the event's timestamp is greater or equal to our Lamport clock, process it
            if timestamp >= LAMPORT_CLOCK:
                LAMPORT_CLOCK = max(LAMPORT_CLOCK, timestamp) + 1   # update lamport clock if necessary
                await self.process_event(event)                     # process the event
            else:
                print(f"Event with timestamp {timestamp} is outdated so we discard it.")

        except Exception as e:
            print(f"Error processing incoming data: {e}")


    async def process_event(self, data):
        global PLAYERS

        if data["type"] == "move":
            pid = str(data["id"])

            if pid not in PLAYERS:
                return

            intended_x = data["x"]
            intended_y = data["y"]

            new_x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], intended_x))
            new_y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], intended_y))

            PLAYERS[str(data["id"])]["x"] = new_x
            PLAYERS[str(data["id"])]["y"] = new_y
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import random
import asyncio
from collections import deque
from heapq import heappush, heappop
from .shared_state import SERVERS, THIS_SERVER, get_primary, update_primary_server
from .database_functions import get_player,get_all_players, update_player_position, get_player_position, delete_player
from .propagate_functions import propagate_food_list_to_replicas, propagate_event_to_replicas

# Constants for world and server configuration:
TICK_RATE = 60
WORLD_BOUNDS = {
    "x_min": 0,
    "x_max": 1000,
    "y_min": 0,
    "y_max": 1000
}
FOOD_COUNT = 20
FOOD_LIST = [] 

# Lamport clock and priority queue:
LAMPORT_CLOCK = 0
EVENT_QUEUE = deque()

# Creates random food positions in the world:
def generate_food():
    global FOOD_LIST
    FOOD_LIST = [
        {"id": i, "x": random.randint(WORLD_BOUNDS["x_min"], WORLD_BOUNDS["x_max"]),
         "y": random.randint(WORLD_BOUNDS["y_min"], WORLD_BOUNDS["y_max"])}
        for i in range(FOOD_COUNT)
    ]

# Handles game connection from proxy (from frontend):
class PlayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global FOOD_LIST

        # Adding players to group:
        self.room_name= "game_room"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # Start the game loop (for server tick rate):
        self.game_loop_task = asyncio.create_task(self.game_loop())

        # Generating a food list in none is initialized:
        if not FOOD_LIST:
            generate_food()
            await propagate_food_list_to_replicas(FOOD_LIST)   # Notify replicas of new food list

        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]  # Get player id from url
        players = await get_all_players()                                # Get player from DB

        # Sends connecting websocket the pre-existing players
        await self.send(json.dumps({
            "type": "all_players", 
            "players": {str(player["id"]): player for player in players},
            "food": FOOD_LIST
        }))

        player = await get_player(self.player_id)                       # Get current player

        # Broadcast to other sockets in group of newly joined player:
        await self.broadcast({
            "type": "player_joined",
            "id": self.player_id,
            "x": player.x,
            "y": player.y,
            "speed": player.speed,
            "size": player.size,
            "color": player.color,
        })

    # Handles websocket disconnection:
    async def disconnect(self, close_code):
        await delete_player(self.player_id)                             # Remove player from DB
        await self.broadcast({
            "type": "player_left", 
            "id": self.player_id
        })

    def check_collision(self, player, food):
        """
        Check if a player collides with a food piece
        """
        return (player["x"] - food["x"])**2 + (player["y"] - food["y"])**2 <= player["size"]**2


    async def receive(self, text_data):     
        global LAMPORT_CLOCK
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

        # If event's timestamp is newer, add it to the queue:
        if timestamp > LAMPORT_CLOCK:
            LAMPORT_CLOCK = max(LAMPORT_CLOCK, timestamp) + 1
            heappush(EVENT_QUEUE, (timestamp, data))
        else:
            print(f"Discarded event with out-of-order timestamp: {timestamp}")


    async def process_event(self, data):
        if data["type"] == "move":
            pid = str(data["id"])

            intended_x = data["x"]
            intended_y = data["y"]

            new_x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], intended_x))
            new_y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], intended_y))

            await update_player_position(pid, new_x, new_y)


    # Game tick loop:
    async def game_loop(self):
        global EVENT_QUEUE

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

                curr_player = await get_player_position(self.player_id)

                await self.broadcast({
                    "type": "update",
                    "id": self.player_id,
                    "x": curr_player["x"],
                    "y": curr_player["y"]
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
            if timestamp > LAMPORT_CLOCK:
                LAMPORT_CLOCK = max(LAMPORT_CLOCK, timestamp) + 1   # update lamport clock if necessary
                await self.process_event(event)                     # process the event
            else:
                print(f"Event with timestamp {timestamp} is outdated so we discard it.")

        except Exception as e:
            print(f"Error processing incoming data: {e}")


    async def process_event(self, data):
        if data["type"] == "move":
            pid = str(data["id"])

            intended_x = data["x"]
            intended_y = data["y"]

            new_x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], intended_x))
            new_y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], intended_y))

            await update_player_position(pid, new_x, new_y)


# When the primary server generates a random food_list, it is received at the backup replicas:
def update_food_list_from_propagation(food_list):
    global THIS_SERVER
    global FOOD_LIST
    FOOD_LIST = food_list
    print(f'Food list was updated at this replica: {THIS_SERVER}')
    

import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Player
import random

"""Functions for accesssing backend database through websockets"""
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
GLOBAL_PLAYERS = {}

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
        "player_inputs": input[]
    }

    """
    players = {} 

    async def connect(self):
        """
        Handles connection of websocket from frontend
        """

        # Adding players to group
        self.room_name= "game_room"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        # Generating a food list in none is initialized
        if not FOOD_LIST:
            generate_food()

        # Get player id from url:
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        player = await get_player(self.player_id)

        # Initializing the player configuration
        GLOBAL_PLAYERS[self.player_id] = {
            "x": 400,  
            "y": 300,
            "size": 40,
            "speed": 150,
            "score": player.score,
            "color": player.color,
            "player_inputs": [],
            "last_input_processed": 0,
        }

        # Sends connecting websocket the pre-existing players
        await self.send(json.dumps({
            "type": "all_players", 
            "players": GLOBAL_PLAYERS,
            "food": FOOD_LIST
            }))

        # Broadcast to other socket in group of joined player
        await self.broadcast({
            "type": "player_joined",
            "id": self.player_id,
            "x": GLOBAL_PLAYERS[self.player_id]["x"],
            "y": GLOBAL_PLAYERS[self.player_id]["y"],
            "speed": GLOBAL_PLAYERS[self.player_id]["speed"],
            "size": GLOBAL_PLAYERS[self.player_id]["size"],
            "color": GLOBAL_PLAYERS[self.player_id]["color"],
        })


    async def disconnect(self, close_code):
        """
        Handles disconnected websocket
        """
        if self.player_id in GLOBAL_PLAYERS:
            del GLOBAL_PLAYERS[self.player_id]
        
            await self.broadcast({"type": "player_left", "id": self.player_id})

    
    def check_collision(self,player, food):
        """
        Check if a player collides with a food piece
        """
        return (player["x"] - food["x"])**2 + (player["y"] - food["y"])**2 <= player["size"]**2


    async def receive(self, text_data):
        """
        Receive a message from the WebSocket
        """
        data = json.loads(text_data)
        
        try:
            player = await get_player(self.player_id)
        except player.DoesNotExist:
            await self.send(json.dumps({"error": "Player not found"}))
            return
        
        if data["type"] == "move":
            if str(data["id"]) in GLOBAL_PLAYERS:
                GLOBAL_PLAYERS[str(data["id"])]["player_inputs"].append({
                    "input_number": data["input_number"],
                    "direction": data["direction"],
                })

        if data["type"] == "ping":
            await self.send(text_data=json.dumps({
                "type": "pong",
                "time": data["time"]
            }))
    
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







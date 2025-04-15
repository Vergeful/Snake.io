import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Player
import random
from .game_logic.game_util import generate_food
from .game_logic.game_config import FOOD_LIST, GLOBAL_PLAYERS, WORLD_BOUNDS
from .database_functions import *
import time 


"""Functions for accesssing backend database through websockets"""
@database_sync_to_async
def get_player(player_id):
    from .models import Player
    return Player.objects.get(id=player_id)

@database_sync_to_async
def save_player(player):
    from .models import Player
    player.save()

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
            print("generating food")
            generate_food()

        # Get player id from url:
        self.player_id = int(self.scope["url_route"]["kwargs"]["player_id"])
        player = await get_player(self.player_id)

        # Initializing the player configuration
        # GLOBAL_PLAYERS[self.player_id] = {
        #     "x": player.x,  
        #     "y": player.y,
        #     "size": player.size,
        #     "speed": player.speed,
        #     "score": player.score,
        #     "color": player.color,
        #     "player_inputs": [],
        #     "last_input_processed": 0,
        #     "name": player.name
        # }

        for player in await get_all_players():
            GLOBAL_PLAYERS[player["id"]] = {
                "x": player["x"],  
                "y": player["y"],
                "size": player["size"],
                "speed": player["speed"],
                "score": player["score"],
                "color": player["color"],
                "player_inputs": [],
                "last_input_processed": 0,
                "name": player["name"]
            }


        # Sends connecting websocket the pre-existing players
        await self.send(json.dumps({
            "type": "all_players", 
            "players": GLOBAL_PLAYERS,
            "food": FOOD_LIST
            }))

        # Broadcast to other socket in group of joined player
        await broadcast({
            "type": "player_joined",
            "id": self.player_id,
            "x": GLOBAL_PLAYERS[self.player_id]["x"],
            "y": GLOBAL_PLAYERS[self.player_id]["y"],
            "speed": GLOBAL_PLAYERS[self.player_id]["speed"],
            "size": GLOBAL_PLAYERS[self.player_id]["size"],
            "color": GLOBAL_PLAYERS[self.player_id]["color"],
            "name": GLOBAL_PLAYERS[self.player_id]["name"],
        })


    async def disconnect(self, close_code):
        """
        Handles disconnected websocket (e.g., tab closed)
        """
        print(f"Disconnected player {self.player_id} with code {close_code}")

        await self.channel_layer.group_discard(self.room_name, self.channel_name)

        if self.player_id in GLOBAL_PLAYERS:
            del GLOBAL_PLAYERS[self.player_id]
            await delete_player(self.player_id)

            await broadcast({
                "type": "player_left",
                "id": self.player_id
            })


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
            if data["id"] in GLOBAL_PLAYERS:
                GLOBAL_PLAYERS[data["id"]]["player_inputs"].append({
                    "input_number": data["input_number"],
                    "direction": data["direction"],
                })

        if data["type"] == "ping":
            GLOBAL_PLAYERS[self.player_id]["last_ping"] = time.time()
            await self.send(text_data=json.dumps({
                "type": "pong",
                "time": data["time"]
            }))

        if data["type"] == "player_disconnected":
            del GLOBAL_PLAYERS[self.player_id]
            await delete_player(self.player_id)

            await broadcast({
                "type": "player_left",
                "id": self.player_id
            })
    

    
    async def send_message(self, event):
        """Send the broadcast message to each connected WebSocket"""
        await self.send(text_data=event["message"])


async def broadcast(message):
    """ Sends a message to all connected WebSockets"""
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "game_room",
        {
            "type": "send_message",
            "message": json.dumps(message),  # Ensure message is JSON string
        }
    )









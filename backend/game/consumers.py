import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Player
import random



WORLD_BOUNDS = {
    "x_min": 0,
    "x_max": 1000,
    "y_min": 0,
    "y_max": 1000
}

FOOD_COUNT = 20
FOOD_LIST = [] 

def generate_food():
    """Creates random food positions in the world"""
    global FOOD_LIST
    FOOD_LIST = [
        {"id": i, "x": random.randint(WORLD_BOUNDS["x_min"], WORLD_BOUNDS["x_max"]),
         "y": random.randint(WORLD_BOUNDS["y_min"], WORLD_BOUNDS["y_max"])}
        for i in range(FOOD_COUNT)
    ]

@database_sync_to_async
def get_player(player_id):
    from .models import Player
    return Player.objects.get(id=player_id)

@database_sync_to_async
def save_player(player):
    from .models import Player
    player.save()

class PlayerConsumer(AsyncWebsocketConsumer):
    players = {} 

    async def connect(self):
        self.room_name= "game_room"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

        if not FOOD_LIST:
            generate_food()

        # Get player id from url:
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        player = await get_player(self.player_id)

        self.players[self.player_id] = {
            "x": 400,  
            "y": 300,
            "size": 40,
            "score": player.score,
            "color": player.color,  
        }

        await self.send(json.dumps({
            "type": "all_players", 
            "players": self.players,
            "food": FOOD_LIST
            }))

        await self.send(json.dumps({
            "type": "player_joined",
            "id": self.player_id,
            "x": self.players[self.player_id]["x"],
            "y": self.players[self.player_id]["y"],
            "color": self.players[self.player_id]["color"],
        }))

        await self.broadcast({
            "type": "info",
            "message": "Testing"
        })

    async def disconnect(self, close_code):
        # Leave websocket group
        if self.player_id in self.players:
            del self.players[self.player_id]
        
            await self.send(json.dumps({"type": "player_left", "id": self.player_id}))

    def check_collision(self,player, food):
        """Check if a player collides with a food piece"""
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

        if data.get("action") == "increase_score":
            # Increment score
            player.score += 1

            # Increase speed at score milestones
            if player.score == 5 or player.score == 10:
                player.speed += 100

            await save_player(player)

            # Send updated data to the frontend
            await self.send(json.dumps({"score": player.score, "speed": player.speed}))
        
        if data["type"] == "move":
            print(data["id"])
            print(self.players)
            if str(data["id"]) in self.players:

                intended_x = data["x"]
                intended_y = data["y"]


                new_x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], intended_x))
                new_y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], intended_y))

                self.players[str(data["id"])]["x"] = new_x
                self.players[str(data["id"])]["y"] = new_y

                global FOOD_LIST
                for food in FOOD_LIST[:]:  # Iterate over food list
                    if self.check_collision(self.players[str(data["id"])], food):
                        FOOD_LIST.remove(food)  # Remove food from list

                        player.score += 1

                        await save_player(player)

                        # Broadcast food removal and player growth
                        await self.send(json.dumps({
                            "type": "food_eaten",
                            "id": food["id"],
                            "player_id": data["id"],
                            "score": player.score
                        }))

                await self.send(json.dumps({
                    "type": "update",
                    "id": data["id"],
                    "x": new_x,
                    "y": new_y
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




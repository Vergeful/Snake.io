import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

@database_sync_to_async
def get_player(player_id):
    from .models import Player
    return Player.objects.get(id=player_id)

@database_sync_to_async
def save_player(player):
    from .models import Player
    player.save()

class PlayerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get player id from url:
        self.player_id = self.scope["url_route"]["kwargs"]["player_id"]
        self.group_name = f"player_{self.player_id}"

        # Join Websocket group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave websocket group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

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

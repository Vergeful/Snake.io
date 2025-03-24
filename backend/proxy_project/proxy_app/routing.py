from django.urls import re_path
from .consumer_handler import GameConsumer

# Tells Django that when a WebSocket connection is made to ws://127.0.0.1:8000/ws/game/<player_id>/,it should use the PlayerConsumer class to handle it
websocket_urlpatterns = [
re_path(r"ws/game/(?P<player_id>\d+)/?$", GameConsumer.as_asgi()),
]

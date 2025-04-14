from django.urls import re_path
from .consumers import PlayerConsumer

# Tells Django that when a WebSocket connection is made to ws://127.0.0.1:8003/ws/game/<player_id>/,it should use the PlayerConsumer class to handle it
websocket_urlpatterns = [
    re_path(r"ws/game/(?P<player_id>\d+)/?$", PlayerConsumer.as_asgi()),
]
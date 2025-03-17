from django.urls import re_path
from .consumers import PlayerConsumer

# Tells Django that when a WebSocket connection is made to ws://127.0.0.1:8020/ws/game/,it should use the PlayerConsumer class to handle it
websocket_urlpatterns = [
    re_path(r"ws/game/$", PlayerConsumer.as_asgi()),
]
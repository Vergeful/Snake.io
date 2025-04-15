from django.urls import re_path
from .consumers import PlayerConsumer, ReplicaConsumer

# Tells Django that when a WebSocket connection is made to ws://127.0.0.1:8001/ws/game/<player_id>/,it should use the PlayerConsumer class to handle it
websocket_urlpatterns = [
    re_path(r"ws/game/(?P<player_id>\d+)/?$", PlayerConsumer.as_asgi()),
        re_path(r"ws/propagated_data/?$", ReplicaConsumer.as_asgi()),
]
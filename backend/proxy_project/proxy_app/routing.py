from django.urls import re_path
from . import consumer_handler

websocket_urlpatterns = [
    re_path(r'ws/game/$', consumer_handler.GameConsumer.as_asgi()),
]

from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Player
from .serializers import PlayerSerializer
import requests

SERVERS = ['http://localhost:8000', 'http://localhost:8001', 'http://localhost:8002']
PRIMARY_SERVER = SERVERS[0]

@api_view(["POST"])
def create_player(request):
    serializer = PlayerSerializer(data=request.data)
    if serializer.is_valid():
        player = serializer.save()   # Save to database

        # If this server is the primary replica, propagate the request to other replicas:
        if is_primary():
            propagate_to_replicas(request)

        return Response(
            {"message": "Player created!", "player_id": player.id},
            status = status.HTTP_201_CREATED
        )
    
    # Error encountered
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Check if this server is the primary replica
def is_primary():
    return get_current_server_url() == PRIMARY_SERVER

# URL for initial primary replica
def get_current_server_url():
    return 'http://localhost:8000'  

# Send the POST request to the other replicas if you are the primary
def propagate_to_replicas(data):
    for server in SERVERS:
        if server != get_current_server_url():
            try:
                requests.post(f'{server}/game/create_player/', data=data, timeout=2)
            except requests.exceptions.RequestException as e:
                print(f"Failed to propagate to {server}: {e}")

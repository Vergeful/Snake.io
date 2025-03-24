from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Player
from .serializers import PlayerSerializer
import requests
from .shared_state import SERVERS, THIS_SERVER, get_primary, update_primary, PRIORITY
 
  
@api_view(["POST"])
def create_player(request):
    data = request.POST.dict()
    print('What we get: ', data)

    serializer = PlayerSerializer(data=data)
    if serializer.is_valid():
        player = serializer.save()   # Save to database

        print(player.id)

        # If this server is the primary replica, propagate the request to other replicas:
        if is_primary():
           propagate_to_replicas(data)

        return Response(
            {"message": "Player created!", "player_id": player.id},
            status = status.HTTP_201_CREATED
        )
     
    # Error encountered
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
# Check if this server is the primary replica
def is_primary():
    global THIS_SERVER
    current_primary_server = get_primary()
    return THIS_SERVER == current_primary_server
 
 
# Send the POST request to the other replicas if you are the primary
def propagate_to_replicas(data):
    global SERVERS
    global THIS_SERVER
    for server in SERVERS:
        if server != THIS_SERVER:
            try:
                requests.post(f'http://{server}/replica/create_player/', data=data, timeout=2)
            except requests.exceptions.RequestException:
                print(f"Server did not respond: {server}")
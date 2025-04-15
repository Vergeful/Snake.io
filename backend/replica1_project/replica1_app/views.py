from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Player
from .serializers import PlayerSerializer
import requests
from .shared_state import SERVERS, THIS_SERVER, get_primary, update_primary_server
from .consumers import update_food_list_from_propagation
import random

 
  
@api_view(["POST"])
def create_player(request):
    data = request.data.copy()      # Make a mutable copy
    print('What we get: ', data)

    # Inject random spawn coordinates within world bounds
    data.setdefault("x", random.randint(100, 900))
    data.setdefault("y", random.randint(100, 900))

    serializer = PlayerSerializer(data=data)
    if serializer.is_valid():
        player = serializer.save()   # Save to database

        print(player.id, player.x, player.y, player.size, player.speed, player.score, player.color)

        # If this server is the primary replica, propagate the request to other replicas:
        if is_primary():
           data["id"] = player.id   # Add ID when primary propagates so that replicas have same ids for same players
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

@api_view(["GET"])
def health_check(request):
     return Response(
            {"status": "OK"},
            status = status.HTTP_200_OK
        )

@api_view(["POST"])
def update_primary(request):
    global THIS_SERVER
    global SERVERS

    data = request.data
    new_primary_server_index = data.get("new_index")
    update_primary_server(SERVERS[new_primary_server_index])
    return Response(
            {"message": f'Primary was updated to {SERVERS[new_primary_server_index]}'},
            status = status.HTTP_200_OK
        )

@api_view(["POST"])
def update_local_food_list(request):
    food_list = request.data.get("food_list", [])
    #  Update food list that is used in the consumer socket:
    update_food_list_from_propagation(food_list)
    return Response({"status": "ok", "received_count": len(food_list)})

import random
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Player
from .serializers import PlayerSerializer


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

        return Response(
            {"message": "Player created!", "player_id": player.id},
            status = status.HTTP_201_CREATED
        )
    # Error encountered
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

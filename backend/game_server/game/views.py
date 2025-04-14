from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Player
from .serializers import PlayerSerializer

@api_view(["POST"])
def create_player(request):
    serializer = PlayerSerializer(data=request.data)
    if serializer.is_valid():
        player = serializer.save()   # Save to database
        return Response(
            {"message": "Player created!", "player_id": player.id},
            status = status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def index(request):
    return HttpResponse("Hello, world. You're at the game index.")
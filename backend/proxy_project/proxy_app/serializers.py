from rest_framework import serializers
from .models import Player

# Validates the incoming data and convert it to a Django model instance.
class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id", "name", "color", "x", "y", "speed", "score", "size"]
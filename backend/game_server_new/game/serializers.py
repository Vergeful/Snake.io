from rest_framework import serializers
from .models import Player

# Validates the incoming data and convert it to a Django model instance.

class PlayerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Allow id to be set manually

    class Meta:
        model = Player
        fields = '__all__'
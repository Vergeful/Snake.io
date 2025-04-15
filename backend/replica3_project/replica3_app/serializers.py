from rest_framework import serializers
from .models import Player

class PlayerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Allow id to be set manually

    class Meta:
        model = Player
        fields = '__all__'
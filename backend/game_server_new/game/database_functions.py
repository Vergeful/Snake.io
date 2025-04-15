from channels.db import database_sync_to_async

@database_sync_to_async
def get_player(player_id):
    from .models import Player
    player = Player.objects.get(id=player_id)
    print(f'Player with id {player_id} retrieved. x = {player.x} y = {player.y}')
    return Player.objects.get(id=player_id)

@database_sync_to_async
def get_all_players():
    from .models import Player
    return list(Player.objects.all().values("id", "name", "x", "y", "size", "speed", "score", "color"))


@database_sync_to_async
def update_player_position(player_id, x, y):
    from .models import Player
    try:
        player = Player.objects.get(id=player_id)
        player.x = x
        player.y = y
        player.save()
        print(f'Player with id {player_id} updated with x = {player.x} and player y = {player.y}')
    except Player.DoesNotExist:
        print(f'Player with id {player_id} does not exist.')

@database_sync_to_async
def get_player_position(player_id):
    from .models import Player
    player = Player.objects.get(id=player_id)
    return {"x": player.x, "y": player.y}

@database_sync_to_async
def delete_player(player_id):
    from .models import Player
    try:
        Player.objects.get(id=player_id).delete()
    except Player.DoesNotExist:
        print(f'PLayer with id {player_id} does not exist.')
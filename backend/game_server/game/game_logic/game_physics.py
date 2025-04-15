from game.game_logic.game_config import GLOBAL_PLAYERS, FOOD_LIST
from game.consumers import broadcast
from game.game_logic.game_config import WORLD_BOUNDS
from game.game_logic.game_util import spawn_food
from game.database_functions import *

TICK_RATE = 60

def check_collision(x1, y1, r1, x2, y2, r2):
    dx = x1 - x2
    dy = y1 - y2
    distance_squared = dx * dx + dy * dy
    return distance_squared <= (r1 - r2) * (r1 - r2)

async def process_game_tick():
    # Process player inputs and update positions
    for player in GLOBAL_PLAYERS:
        if GLOBAL_PLAYERS[player]["player_inputs"]:
            player_input = GLOBAL_PLAYERS[player]["player_inputs"][-1]
            GLOBAL_PLAYERS[player]["player_inputs"].clear()

            direction = player_input["direction"]
            speed = GLOBAL_PLAYERS[player]["speed"]

            dx = direction["dx"] * speed / TICK_RATE
            dy = direction["dy"] * speed / TICK_RATE

            x = GLOBAL_PLAYERS[player]["x"] + dx
            y = GLOBAL_PLAYERS[player]["y"] + dy

            x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], x))
            y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], y))

            GLOBAL_PLAYERS[player]["x"] = x
            GLOBAL_PLAYERS[player]["y"] = y
            GLOBAL_PLAYERS[player]["last_input_processed"] = player_input["input_number"]

    # Handle food collision
    for player_id, player in GLOBAL_PLAYERS.items():
        for food in FOOD_LIST[:]:
            if check_collision(player["x"], player["y"], player["size"], food["x"], food["y"], 5):
                FOOD_LIST.remove(food)
                player["score"] += 1
                player["size"] += 1  # Simple growth mechanic
                new_food = spawn_food()

                await broadcast({
                    "type": "food_eaten",
                    "id": food["id"],
                    "player_id": player_id,
                    "score": player["score"],
                    "size": player["size"]
                })

                await broadcast({
                    "type": "spawn_food",
                    "food": new_food 
                })

    # Handle player collision (like agar.io)
    players = list(GLOBAL_PLAYERS.items())
    for i, (id_a, a) in enumerate(players):
        for id_b, b in players[i + 1:]:
            if id_a not in GLOBAL_PLAYERS or id_b not in GLOBAL_PLAYERS:
                continue
            if a["size"] > b["size"] and check_collision(a["x"], a["y"], a["size"], b["x"], b["y"], b["size"]):
                a["score"] += b["score"]
                a["size"] += int(b["size"] * 0.5)
                await broadcast({
                    "type": "player_eaten",
                    "id_eater": id_a, 
                    "id": id_b,
                    "size": a["size"]
                })
                del GLOBAL_PLAYERS[id_b]
                await delete_player(id_b)
                break
            elif b["size"] > a["size"] and check_collision(b["x"], b["y"], b["size"], a["x"], a["y"], a["size"]):
                b["score"] += a["score"]
                b["size"] += int(a["size"] * 0.5)
                await broadcast({
                    "type": "player_eaten",
                    "id_eater": id_b, 
                    "id": id_a,
                    "size": b["size"]
                })
                del GLOBAL_PLAYERS[id_a]
                await delete_player(id_a)
                break

    # Broadcast updated positions
    for player in list(GLOBAL_PLAYERS):
        await broadcast({
            "type": "update",
            "id": player,
            "x": GLOBAL_PLAYERS[player]["x"],
            "y": GLOBAL_PLAYERS[player]["y"],
            "last_input_processed": GLOBAL_PLAYERS[player]["last_input_processed"]
        })
    

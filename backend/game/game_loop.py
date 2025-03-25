import asyncio
import time
# from .game_state import GLOBAL_PLAYERS
from .consumers import WORLD_BOUNDS, GLOBAL_PLAYERS
import json

TICK_RATE = 60
TICK_DURATION = 1 / TICK_RATE


async def global_game_loop():
    """ Runs the game loop independently from WebSockets"""

    try:
        while True:
            if GLOBAL_PLAYERS:
                break  # Exit loop once a player joins

            print("Still waiting for players...")
            await asyncio.sleep(1 / TICK_RATE)

        tick_counter = 0
        next_tick = time.perf_counter()  # more precise than time.time()
        timer_test = time.perf_counter()

        while True:
            tick_counter += 1
            tick_start = time.perf_counter()
            
            #----[ GAME LOGIC ]--------

            for player in GLOBAL_PLAYERS:
                if GLOBAL_PLAYERS[player]["player_inputs"]:
                    print("processing...")
                    player_input = GLOBAL_PLAYERS[player]["player_inputs"][-1]
                    GLOBAL_PLAYERS[player]["player_inputs"].clear()

                    directions = player_input["direction"]

                    intended_x = GLOBAL_PLAYERS[player]["x"] + GLOBAL_PLAYERS[player]["speed"] * directions["dx"] * 1/TICK_RATE
                    intended_y = GLOBAL_PLAYERS[player]["y"] + GLOBAL_PLAYERS[player]["speed"] * directions["dy"] * 1/TICK_RATE

                    new_x = max(WORLD_BOUNDS["x_min"], min(WORLD_BOUNDS["x_max"], intended_x))
                    new_y = max(WORLD_BOUNDS["y_min"], min(WORLD_BOUNDS["y_max"], intended_y))

                    GLOBAL_PLAYERS[player]["x"] = new_x
                    GLOBAL_PLAYERS[player]["y"] = new_y
                    GLOBAL_PLAYERS[player]["last_input_processed"] = player_input["input_number"]

            for player in GLOBAL_PLAYERS:
                asyncio.create_task(broadcast({
                    "type": "update",
                    "id": player,
                    "x": GLOBAL_PLAYERS[player]["x"],
                    "y": GLOBAL_PLAYERS[player]["y"],
                    "last_input_processed": GLOBAL_PLAYERS[player]["last_input_processed"]
                }))

            
            #---------------------

            # Calculate next tick time
            next_tick += TICK_DURATION
            sleep_time = max(0, next_tick - time.perf_counter())
            await asyncio.sleep(sleep_time)

            if tick_counter % 60 == 0:
                print("Actual tick time:", time.perf_counter() - timer_test)
                timer_test = time.perf_counter()

    except asyncio.CancelledError:
        pass


async def broadcast(message):
    """ Sends a message to all connected WebSockets"""
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        "game_room",
        {
            "type": "send_message",
            "message": json.dumps(message),  # Ensure message is JSON string
        }
    )

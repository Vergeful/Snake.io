import asyncio
import time
from ..consumers import GLOBAL_PLAYERS
import json
from .game_config import WORLD_BOUNDS
from .game_physics import process_game_tick

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
        next_tick = time.perf_counter() 
        timer_test = time.perf_counter()

        while True:
            tick_counter += 1
            
            #----[ GAME LOGIC ]--------

            await process_game_tick()

            
            #---------------------

            # Calculate next tick time
            next_tick += TICK_DURATION
            sleep_time = max(0, next_tick - time.perf_counter())
            await asyncio.sleep(sleep_time)

            # For debugging
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

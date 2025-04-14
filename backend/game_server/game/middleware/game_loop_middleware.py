import asyncio
from game.game_logic.game_loop import global_game_loop

class GameLoopMiddleware:
    def __init__(self, app):
        self.app = app
        self.loop_started = False

    async def __call__(self, scope, receive, send):
        # Run the game loop only once (on the first connection)
        if not self.loop_started:
            self.loop_started = True
            print("Starting global game loop...")
            asyncio.create_task(global_game_loop())  # run in current loop

        # Continue processing WebSocket or HTTP
        await self.app(scope, receive, send)

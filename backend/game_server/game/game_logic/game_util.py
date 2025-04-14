from .game_config import FOOD_COUNT, FOOD_LIST, WORLD_BOUNDS
import random

def generate_food():
    """
    Creates random food positions in the world
    """
def generate_food():
    FOOD_LIST.clear() 
    for i in range(FOOD_COUNT):
        FOOD_LIST.append({
            "id": i,
            "x": random.randint(WORLD_BOUNDS["x_min"], WORLD_BOUNDS["x_max"]),
            "y": random.randint(WORLD_BOUNDS["y_min"], WORLD_BOUNDS["y_max"])
        })

def spawn_food():
    global FOOD_COUNT
    FOOD_COUNT += 1
    food_id = FOOD_COUNT
    food_obj = {
        "id": food_id,
        "x": random.randint(WORLD_BOUNDS["x_min"], WORLD_BOUNDS["x_max"]),
        "y": random.randint(WORLD_BOUNDS["y_min"], WORLD_BOUNDS["y_max"])
    }
    FOOD_LIST.append(food_obj)
    return food_obj 
import websockets
import json
import requests
from .shared_state import SERVERS, THIS_SERVER
from .replica_connection_manager import REPLICA_MANAGER

# Send created food list to replicas on initial connection:
async def propagate_food_list_to_replicas(food_list):
    global SERVERS
    global THIS_SERVER
    for server in SERVERS:
        if server != THIS_SERVER:
            try:
                # This endpoint has not been created yet:
                response = requests.post(f"http://{server}/replica/update_food_list/", data={"food_list": food_list})
                if response.status_code == 200:
                    print(f"Successfully sent food list to {server}")
                else:
                    print(f"Failed to send food list to {server}")
            except:
                print(f"Server did not respond: {server}")

# Send event to replicas over websocket:
async def propagate_event_to_replicas(event_data):
    global SERVERS
    global THIS_SERVER
    # Send WebSocket messages to all replica servers
    for server in SERVERS:
        if server != THIS_SERVER:
            await REPLICA_MANAGER.send(server, json.dumps(event_data))
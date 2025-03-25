# Helper functions to help with leader election
import requests
from .shared_state import SERVERS, get_primary, update_primary, PRIORITY

def is_server_healthy(server_url):
    try:
        response = requests.get(f"http://{server_url}/replica/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def check_alive_servers():
    # Return an array of [(index, server_url)] for alive servers.
    # The index is for the SERVERS array where higher priorities are at lower indices.
    alive_servers = []
    for index, server in enumerate(SERVERS):
        if is_server_healthy(server):
            alive_servers.append((index, server))
    return alive_servers

def notify_replicas(new_primary_server_index):
    for server in SERVERS:
        try:
            response = requests.post(f"http://{server}/replica/update_primary", json={"new_index": new_primary_server_index})
            if response.status_code == 200:
                print(f"Replica updated with new primary: {server}")
        except requests.RequestException:
                print(f"Failed to notify this replica about the new primary: {server}")
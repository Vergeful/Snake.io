import requests
import json
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .shared_state import SERVERS, PRIORITY, get_primary, update_primary
from .leader_functions import check_alive_servers, notify_replicas
from django.utils.decorators import sync_and_async_middleware
import time

@csrf_exempt
@sync_and_async_middleware
async def create_player(request):
    if request.method == 'POST':
        data = request.body
    try:
        response = await send_to_primary(data)
        # Ensure the response is JSON-serializable before returning
        if isinstance(response, dict):
            return JsonResponse(response, safe=False)
        elif isinstance(response, str):
            return JsonResponse({"message": response}, safe=False)
        else:
            return JsonResponse({"message": "Unexpected error occurred"}, status=500)
    except Exception as e:
        print(f"Error in create_player: {e}")
        return JsonResponse({"message": "An error occurred while processing the request."}, status=500)

async def send_to_primary(data):
    primary_server = get_primary()
    try:
        json_data = json.loads(data.decode('utf-8'))
        # If primary server is working:
        response = requests.post(f'http://{primary_server}/replica/create_player/', data=json_data, timeout=2)
        print(f'Successfully sent to the primary server: {primary_server}')
        return response.json()
    except requests.exceptions.RequestException:
        print(f"Primary replica could not be reached: {primary_server}")
        # If primary server is not working, we need to trigger a leader election to designate a backup server as the primary:
        response = trigger_leader_election()

        if response is None:
            return {"message": "No backup replicas could be reached"}

        # Wait briefly for the new primary to propagate changes
        time.sleep(2)
        primary_server = get_primary()

        # Resend data to new primary server:
        try:
            json_data = json.loads(data.decode('utf-8'))
            # If new primary server is working:
            response = requests.post(f'http://{primary_server}/replica/create_player/', data=json_data, timeout=2)
            print(f'Successfully sent to the new primary server: {primary_server}')
            return response.json()
        except Exception:
            print(f'New primary replica could not be reached {primary_server}')
            return {"message": f'New primary replica could not be reached {primary_server}'}

# PROXY LEADER ELECTION:
# 1. Send a health check to all other servers, with a small timeout.
# 2. Get ids from backup replicas that respond.
# 3. Choose new primary replica based on highest id.
# 4. Send id of new primary replica to backup replicas that respond.
# 5. All backup replicas will update who the new primary replica is locally.
def trigger_leader_election():
    print("Leader election started...")

    alive_servers =  check_alive_servers()

    if not alive_servers:
        print("No alive servers found during leader election.")
        return None  # Explicitly return None for clarity
    
    # Sort array so that servers with lower indices are lowest in the SERVERS array.
    # These servers at lower indices have higher priorities.
    sorted_alive_servers = sorted(alive_servers, key=lambda x: x[0])

    # Get replica with highest priority that responded:
    new_primary_server_index , new_primary_server = sorted_alive_servers[0]
    print(f'New primary server: {new_primary_server}')
    update_primary(new_primary_server)
    notify_replicas(new_primary_server_index)

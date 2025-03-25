import requests
import json
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .shared_state import SERVERS, PRIORITY, get_primary, update_primary
from .leader_functions import check_alive_servers, notify_replicas

@csrf_exempt
def create_player(request):
    if request.method == 'POST':
        data = request.body
        response = send_to_primary(data)
        return JsonResponse(response)

def send_to_primary(data):
    primary_server = get_primary()
    try:
        json_data = json.loads(data.decode('utf-8'))
        # If primary server is working:
        response = requests.post(f'http://{primary_server}/replica/create_player/', data=json_data, timeout=60)
        print(f'Successfully sent to the primary server: {primary_server}')
        return response.json()
    except requests.exceptions.RequestException:
        print(f"Primary replica could not be reached: {primary_server}")
        # If primary server is not working, we need to trigger a leader election to designate a backup server as the primary:
        response = trigger_leader_election()
        primary_server = get_primary()
        print(f'Successfully sent to new primary server: {primary_server}')
        return response.json()

# PROXY LEADER ELECTION:
# 1. Send a health check to all other servers, with a small timeout.
# 2. Get ids from backup replicas that respond.
# 3. Choose new primary replica based on highest id.
# 4. Send id of new primary replica to backup replicas that respond.
# 5. All backup replicas will update who the new primary replica is locally.
async def trigger_leader_election(self):
    print("Leader election started...")
    print("But for real this time")

    alive_servers = check_alive_servers()

    if not alive_servers:
        return Response(
            {"error": "Primary and all backup replicas are unavailable."},
            status = status.HTTP_400_BAD_REQUEST
        )
    
    # Sort array so that servers with lower indices are lowest in the SERVERS array.
    # These servers at lower indices have higher priorities.
    sorted_alive_servers = sorted(alive_servers, key=lambda x: x[0])

    # Get replica with highest priority that responded:
    new_primary_server_index , new_primary_server = sorted_alive_servers[0]
    print(f'New primary server: {new_primary_server}')
    update_primary(new_primary_server)
    notify_replicas(new_primary_server_index)

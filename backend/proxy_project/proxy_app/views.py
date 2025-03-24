import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .shared_state import SERVERS, PRIORITY, get_primary, update_primary

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
        response = requests.post(f'http://{primary_server}/replica/create_player/', data=json_data, timeout=2)
        print(f'Successfully sent to the primary server: {primary_server}')
        return response.json()
    except requests.exceptions.RequestException:
         print(f"Primary replica could not be reached: {primary_server}")
        # If primary server is not working, we need to trigger a leader election to designate a backup server as the primary:


    return {'error': 'All servers could not be reached.'}


async def trigger_leader_election(self):
    pass
import requests
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

SERVERS = ['http://localhost:8001', 'http://localhost:8002', 'http://localhost:8003']
PRIMARY_SERVER = SERVERS[0] 

@csrf_exempt
def create_player(request):
    if request.method == 'POST':
        data = request.body
        response = send_to_primary(data)
        return JsonResponse(response)

def send_to_primary(data):
    global PRIMARY_SERVER
    try:
        # If primary server is working:
        json_data = json.loads(data.decode('utf-8'))
        print(json_data)
        response = requests.post(f'{PRIMARY_SERVER}/replica/create_player/', data=json_data, timeout=2)
        print(f'Successfully sent to the primary server: {PRIMARY_SERVER}')
        print(response.json)
        return response.json()
    except requests.exceptions.RequestException:
        # If primary server is not working, we need to designate a backup server as the primary:
        for server in SERVERS:
            if server != PRIMARY_SERVER:
                try:
                    response = requests.post(f'{server}/replica/create_player/', data=data, timeout=2)
                    PRIMARY_SERVER = server  # Set new primary server
                    print(f'Successfully sent to new primary server: {PRIMARY_SERVER}')
                    return response.json()
                except requests.exceptions.RequestException:
                    print(f'Backup server {server} could not be reached.')
    return {'error': 'All servers could not be reached.'}
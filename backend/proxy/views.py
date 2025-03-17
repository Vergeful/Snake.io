from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests

SERVERS = ['http://localhost:8000', 'http://localhost:8001', 'http://localhost:8002']
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
        # If primary server is up
        response = requests.post(f'{PRIMARY_SERVER}/game/create_player/', data=data, timeout=2)
        return response.json()
    except requests.exceptions.RequestException:
        # If primary server is down, find new primary from available replicas
        for server in SERVERS:
            if server != PRIMARY_SERVER:
                try:
                    response = requests.post(f'{server}/game/create_player/', data=data, timeout=2)
                    PRIMARY_SERVER = server
                    return response.json()
                except requests.exceptions.RequestException:
                    continue
    return {'error': 'No server can be reached.'}
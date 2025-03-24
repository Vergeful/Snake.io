import requests
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
        response = requests.post(f'{PRIMARY_SERVER}/replica/create_player/', data=data, timeout=2)
        print(f'Successfully sent to the primary server: {PRIMARY_SERVER}')
        return response.json()
    except requests.exceptions.RequestException:
         print(f"Primary replica could not be reached: {PRIMARY_SERVER}")
        # If primary server is not working, we need to trigger a leader election to designate a backup server as the primary:



    return {'error': 'All servers could not be reached.'}


async def trigger_leader_election(self):
    pass
# Single source of truth for views and consumers files:
import threading

SERVERS = ['localhost:8001', 'localhost:8002', 'localhost:8003', 'localhost:8004', 'localhost:8005']
PRIMARY_SERVER = SERVERS[0]
THIS_SERVER = SERVERS[0]

# For leader election, indices correspond with the server array:
PRIORITY = [5,4,3,2,1]

# Since our application uses multiple threads (Daphne), we need to avoid race conditions:
lock = threading.Lock()

def get_primary():
    with lock:
        return PRIMARY_SERVER

def update_primary_server(new_server):
    with lock:
        global PRIMARY_SERVER

        if PRIMARY_SERVER != new_server:
            PRIMARY_SERVER = new_server

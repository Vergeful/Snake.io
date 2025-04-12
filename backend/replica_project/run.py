import os
import subprocess
import sys

# Step 1: Set the environment variable from command line input
def set_env_variable():
    if len(sys.argv) < 2:
        print("Please provide the value for REPLICA_NUM.")
        sys.exit(1)
    
    replica_num = sys.argv[1]
    os.environ['REPLICA_NUM'] = replica_num
    print(f"REPLICA_NUM set to: {replica_num}")
    return replica_num  # return it for use in other functions

# Step 2: Run makemigrations and migrate
def run_migrations():
    try:
        print("Running makemigrations...")
        subprocess.run(['python', 'manage.py', 'makemigrations'], check=True)

        print("Running migrate...")
        subprocess.run(['python', 'manage.py', 'migrate'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running migrations: {e}")
        sys.exit(1)

# Step 3: Run the Django development server
def run_server(replica_num):
    port = str(8000 + int(replica_num))
    try:
        print(f"Running the server on port {port}...")
        subprocess.run(['python', 'manage.py', 'runserver', f'{port}'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running the server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    replica_num = set_env_variable()
    run_migrations()
    run_server(replica_num)

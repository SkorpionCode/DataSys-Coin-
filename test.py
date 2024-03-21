# Import necessary modules
import socket
import jsonpickle
import yaml
import threading
import requests
import json
import uuid

def send_transaction_id(transaction_id, transaction_data):
    server_address = ('localhost', 9000)

    data = {
        'transaction_id': transaction_id,
        'transaction_data': transaction_data
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(server_address)
            serialized_data = json.dumps(data).encode('utf-8')
            client_socket.sendall(serialized_data)
            print("Transaction ID sent successfully.")
    except Exception as e:
        print(f"Error sending transaction ID: {e}")

class BlockchainClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def create_wallet(self, wallet_id):
        # Check if the keys file exists
        public_key, private_key = self.load_keys(wallet_id)
        if public_key and private_key:
            print(f"Wallet {wallet_id} already exists.")
            return public_key, private_key

        # If keys file does not exist, connect to the server
        try:
            self.client_socket.connect((self.host, self.port))
            request_data = {
                'action': 'create_wallet',
                'wallet_id': wallet_id
            }

            self.client_socket.sendall(jsonpickle.encode(request_data).encode())
            response_data = self.client_socket.recv(1024).decode()

            response_dict = jsonpickle.decode(response_data)

            if response_dict['status'] == 'success':
                public_key = response_dict['public_key']
                private_key = response_dict['private_key']

                # Save keys to YAML file
                key_data = {'public_key': public_key, 'private_key': private_key}
                self.save_keys(wallet_id, key_data)

                return public_key, private_key
            else:
                print(f"Error creating wallet: {response_dict['message']}")
                return None, None
        except Exception as e:
            print(f"Error connecting to the server: {e}")
            return None, None
        finally:
            if self.client_socket:
                self.client_socket.close()

    def save_keys(self, wallet_id, key_data):
        with open(f'dsc-key-{wallet_id}.yaml', 'w') as key_file:
            yaml.dump(key_data, key_file)

    def load_keys(self, wallet_id):
        try:
            with open(f'dsc-key-{wallet_id}.yaml', 'r') as key_file:
                key_data = yaml.safe_load(key_file)
                public_key = key_data['public_key']
                private_key = key_data['private_key']
                return public_key, private_key
        except (FileNotFoundError, yaml.YAMLError):
            return None, None

def receive_messages(client, client_id):
    while True:
        data = client.recv(1024)
        if not data:
            break

        msg = data.decode()
        print(msg)

        # Update balance if a transaction message is received
        if msg.startswith("Transaction ID"):
            parts = msg.split()
            new_balance = int(parts[-1])
            FunctionalityHandler.client_balances[client_id] = new_balance

        print(f"Balance: {FunctionalityHandler.client_balances[client_id]}")


def send_messages(client, client_id):
    while True:
        user_input = input("> ").split()

        if user_input[0] == "send":
            receiver_key = user_input[1]
            amt = int(user_input[2])
            send_req = f"send {receiver_key} {amt}"
            client.send(send_req.encode())

            # Update local balance after sending a transaction
            FunctionalityHandler.client_balances[client_id] -= amt
            print(f"Balance: {FunctionalityHandler.client_balances[client_id]}")

        elif user_input[0] == "balance":
            print(f"Balance: {FunctionalityHandler.client_balances[client_id]}")




def start_registration(client, public_key, client_balances ):
    client_id = str(uuid.uuid4())  # Generate a unique client ID
    FunctionalityHandler.client_balances[client_id] = 100


    receive_thread = threading.Thread(target=receive_messages, args=(client, client_id))
    send_thread = threading.Thread(target=send_messages, args=(client, client_id))

    receive_thread.start()
    send_thread.start()

    # Let the user interact with the system
    while True:
        user_input = input("Enter a command ('send', 'balance', or 'exit'): ")

        if user_input.lower() == "exit":
            print("Exiting registration.")
            break

        if user_input.lower() == "balance":
            print(f"Balance: {FunctionalityHandler.client_balances[client_id]}")

    receive_thread.join()
    send_thread.join()

    client.close()


class FunctionalityHandler:
    client_balances = {}  # Initialize client_balances as a class variable

    def __init__(self):
        self.keywords = []

    def create_functionality(self):
        print("Implementing create functionality")
        # Add your 'create' logic here
        # For example, you can create an object, file, etc.
        # Create a client
        client = BlockchainClient(host="localhost", port=8000)

        # Request to create wallets
        wallet1_public_key, wallet1_private_key = client.create_wallet("77")

        # Display the results
        print("Wallet 1:")
        print(f"Public Key: {wallet1_public_key}")
        print(f"Private Key: {wallet1_private_key}")

    def register_functionality(self):
        print("Implementing register functionality")

        host = "localhost"
        port = 5005

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        client.connect((host, port))
        file_path = "dsc-key-77.yaml"  # Replace with the actual file path

        public_key = read_public_key_from_yaml(file_path)

        if public_key is not None:
            print(f"Public Key: {public_key}")
        else:
            print("Public key is not generated or file not present.")
            exit()

        # Sending the public key to the server
        client.send(public_key.encode())

        client_balances = {}  # Use a local variable for client_balances in this context
        client_balances[public_key] = 100

        #print(f"Connected with Public Key: {public_key}, Balance: {client_balances[public_key]}")
        start_registration(client, public_key, client_balances)
    def process_command(self, command):
        if command.lower() == "create":
            self.create_functionality()
        elif command.lower() == "register":
            self.register_functionality()
        else:
            print("Unknown command. Please try again.")

def read_public_key_from_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
            public_key = data.get('public_key')
            return public_key
    except FileNotFoundError:
        return None
    except yaml.YAMLError as e:
        print(f"Error reading YAML file: {e}")
        return None

def start():
    handler = FunctionalityHandler()

    while True:
        user_input = input("Enter a command ('create', 'register', or 'exit'): ")

        if user_input.lower() == "exit":
            print("Exiting program.")
            break

        handler.process_command(user_input)

# Main block to use the client
if __name__ == "__main__":
    start()
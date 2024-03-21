import socket
import threading

import jsonpickle
import time
from datetime import datetime
import hashlib

class MetronomeServer:
    def __init__(self, host, port, max_connections):
        self.validator_counter = 0
        self.default_difficulty = 30  # Initialize the default difficulty
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.validators = set()
        self.lock = threading.Lock()

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            print(f"Server listening on {self.host}:{self.port}")

            while True:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()

        except Exception as e:
            print(f"Error starting server: {e}")

    def handle_client(self, client_socket):
        try:
            # Receive data from the client
            data = client_socket.recv(1024).decode()
            message = jsonpickle.decode(data)

            if message["action"] == "get_last_difficulty" and message["message"] == "send last difficulty":
                # Respond to the validator's request for the last difficulty
                last_difficulty = self.get_last_difficulty()
                response = {"last_difficulty": last_difficulty}
                response_msg = jsonpickle.encode(response)
                client_socket.sendall(response_msg.encode())

            if message["action"] == "register" and message["message"] == "I am validator":
                validator_no = self.register_validator()

                #Send a response to the client
                response_data = {"message": f"Registered as validator {validator_no}"}
                response_message = jsonpickle.encode(response_data)
                client_socket.sendall(response_message.encode())

        except Exception as e:
            print(f"Error handling client: {e}")


    def get_last_difficulty(self):
        with self.lock:
            num_validators = len(self.validators)

            if num_validators < 4:
                self.default_difficulty = max(1, self.default_difficulty - 1)
            elif num_validators > 8:
                self.default_difficulty += 1

            return self.default_difficulty

    def register_validator(self):
        with self.lock:
            self.validator_counter += 1
            validator_no = self.validator_counter
            self.validators.add(validator_no)

        print(f"Validator {validator_no} registered")
        return validator_no
class MetronomeClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to blockchain server at {self.server_host}:{self.server_port}")
        except Exception as e:
            print(f"Error connecting to server: {e}")

    def generate_hash(self, data):
        # This is a simple hash function; you can use a more secure one
        return hashlib.sha256(data.encode()).hexdigest()

    def send_metronome_data(self):
        while True:
            # Generate a timestamp and some data to hash
            timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
            data_to_hash = f"Timestamp: {timestamp}, Random Data: {timestamp}"

            # Create a hash of the data
            data_hash = self.generate_hash(data_to_hash)

            # Prepare data to send to the server
            data = {'action': 'metronome', 'hash': data_hash, 'timestamp': timestamp}

            try:
                # Send the data to the server
                message = jsonpickle.encode(data)
                self.client_socket.sendall(message.encode())

                # Receive and print the server response
                response = self.client_socket.recv(1024).decode()
                print(f"Server response: {response}")
            except Exception as e:
                print(f"Error sending metronome data: {e}")

            # Wait for 6 seconds before sending the next hash
            time.sleep(6)

    def close_connection(self):
        self.client_socket.close()
        print("Connection closed")

if __name__ == "__main__":
    server_host = "localhost"
    metronome_host = "localhost"
    server_port = 4000
    max_connections = 8
    metronome_port = 8000

    metronome_server = MetronomeServer(server_host, server_port, max_connections)
    metronome_server_thread = threading.Thread(target=metronome_server.start)

    metronome_client = MetronomeClient(metronome_host, metronome_port)
    metronome_client.connect()
    metronome_client_thread = threading.Thread(target=metronome_client.send_metronome_data)

    try:
        metronome_server_thread.start()
        metronome_client_thread.start()
        metronome_server_thread.join()
        metronome_client_thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        metronome_server.server_socket.close()
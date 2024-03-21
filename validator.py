# dsc-validator.py

import sys
import threading
import yaml
import socket
import time
import hashlib
import json
import requests



def add_block_to_server(last_hash, transaction_data, result):
    server_address = ('localhost', 8000)

    data = {
        'action': 'add_block',
        'block_data': {
            'last_hash': last_hash,
            'transaction_data': transaction_data,
            'proof' : result
        }
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(server_address)
            serialized_data = json.dumps(data).encode('utf-8')
            client_socket.sendall(serialized_data)
            print("Data sent successfully.")

            # Receive the response from the server
            response = client_socket.recv(1024)
            result = json.loads(response.decode())
            print(result.get('message', ''))

    except Exception as e:
        print(f"Error communicating with the server: {e}")

def get_transaction():
    server_address = ('localhost', 9000)
    request_data = {'validator_request': True}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(server_address)
            serialized_data = json.dumps(request_data).encode('utf-8')
            client_socket.sendall(serialized_data)

            response_data = client_socket.recv(1024)
            if response_data:
                transaction = json.loads(response_data.decode('utf-8'))
                print(f"Received transaction: {transaction}")
                return transaction
            else:
                print("No transactions available")
                return None
    except Exception as e:
        print(f"Error getting transaction: {e}")
        return None


def confirm_block():
    server_address = ('localhost', 9000)
    request_data = {'confirm_block': True}
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(server_address)
            serialized_data = json.dumps(request_data).encode('utf-8')
            client_socket.sendall(serialized_data)

            response_data = client_socket.recv(1024)
            print(response_data.decode('utf-8'))
    except Exception as e:
        print(f"Error confirming block: {e}")



class Validator:
    def __init__(self, config_file):
        self.config_file = config_file
        self.blockchain_server_address = ('localhost', 8000)
        self.metronome_server_address = ('localhost', 4000)

    def get_last_block_hash(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blockchain_socket:
                blockchain_socket.connect(self.blockchain_server_address)
                blockchain_socket.sendall(b'GET_LAST_BLOCK_HASH')
                last_block_hash = blockchain_socket.recv(1024).decode('utf-8')
                return last_block_hash
        except (socket.error, ConnectionRefusedError) as e:
            print(f"Error connecting to the blockchain server: {e}")
            return None

    def get_hashes_from_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blockchain_socket:
                blockchain_socket.connect(self.blockchain_server_address)
                # Prepare the request message
                request_message = {
                    'action': 'validator_request',
                    'request': 'GET_LAST_METRONOME_BLOCK_HASH'
                }

                # Convert the request message to a JSON-encoded string
                json_request = json.dumps(request_message)

                blockchain_socket.sendall(json_request.encode())  # Send a request to the blockchain server
                received_data = blockchain_socket.recv(1024).decode('utf-8')
                response_data = json.loads(received_data)
                last_metronome_block_hash = response_data.get('last_metronome_block_hash')
                print("the last hash received is:")
                return last_metronome_block_hash
        except (socket.error, ConnectionRefusedError) as e:
            print(f"Error connecting to the blockchain server: {e}")
            return None

    def get_last_difficulty(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as metronome_socket:
                metronome_socket.connect(self.metronome_server_address)
                metronome_socket.sendall(b'GET_LAST_DIFFICULTY')
                last_difficulty = int(metronome_socket.recv(1024).decode('utf-8'))
                return last_difficulty
        except (socket.error, ConnectionRefusedError) as e:
            print(f"Error connecting to the metronome server: {e}")
            return None

    def pow_lookup(self, my_hash_input, hash_lookup, difficulty, blocktime):
        start_time = time.time() * 1000  # current_time() returns milliseconds
        nonce = 0
        while time.time() * 1000 < start_time + blocktime:
            # Using SHA-256
            hash_output = hashlib.sha256((my_hash_input + str(nonce)).encode('utf-8')).hexdigest()
            prefix_hash_lookup = hash_lookup[:difficulty]
            prefix_hash_output = hash_output[:difficulty]
            #print(f"Nonce: {nonce}, Hash Output: {hash_output}, Prefix Lookup: {prefix_hash_lookup}, Prefix Output: {prefix_hash_output}")

            if prefix_hash_lookup == prefix_hash_output:
                return nonce
            else:
                nonce += 1

        return -1

    def pom_write(self, memory_store, my_hash_input, num_hashes):
        for i in range(num_hashes):
            hash_output = hashlib.sha256((my_hash_input + str(i)).encode('utf-8')).hexdigest()
            memory_store.append((hash_output, i))

        # Sort the memory_store based on hash value
        memory_store.sort(key=lambda x: x[0])

        return True

    def pom_lookup(self, memory_store, hash_lookup, difficulty):
        prefix_hash_lookup = hash_lookup[:difficulty]

        # Binary search for prefix_hash_lookup in memory_store
        low, high = 0, len(memory_store) - 1

        while low <= high:
            mid = (low + high) // 2
            mid_hash = memory_store[mid][0]

            if mid_hash == prefix_hash_lookup:
                return memory_store[mid][1], mid + 1  # Return NONCE and number of lookups
            elif mid_hash < prefix_hash_lookup:
                low = mid + 1
            else:
                high = mid - 1

        return -1, len(memory_store)  # Not found

    def validate(self):
        config = self.load_config()
        if not config or not self.check_config_fields(config):
            print("Error: Invalid or incomplete config file.")
            sys.exit(1)

        while True:
            # Connect to blockchain server and get the last block hash
            last_block_hash = self.get_hashes_from_server()
            print(last_block_hash)
            if last_block_hash is None:
                print("Error getting hashes from the blockchain server.")
                sys.exit(1)


            # Connect to metronome server and get the last difficulty setting
            #last_difficulty = self.get_last_difficulty()
            last_difficulty = 6
            #if last_difficulty is None:
                #print("Metronome server will be online for checkpoint 2. Using default difficulty 30.")
                #last_difficulty = 30

            # Extract prefix based on difficulty
            prefix_length = min(last_difficulty, len(last_block_hash))
            prefix = last_block_hash[:prefix_length]

            # Query the appropriate PoW, PoM, or PoS server
            proof_type = config["proof"]
            if proof_type == "pow":
                result = self.pow_lookup(f"{config['fingerprint']}{config['public_key']}", last_block_hash, last_difficulty,
                                         6000)
            elif proof_type == "pom":
                memory_store = []
                num_hashes = int(config["pom"]["num_hashes"])

                print(f"gen/org {num_hashes} hashes using {config['pom']['num_passes']} passes")
                start_time = time.time()
                for i in range(int(config["pom"]["num_passes"])):
                    print(f"generating hashes [Thread #{i + 1}]")
                    t = threading.Thread(target=self.pom_write,
                                         args=(memory_store, f"{config['fingerprint']}{config['public_key']}", num_hashes))
                    t.start()

                for thread in threading.enumerate():
                    if thread != threading.current_thread():
                        thread.join()

                print("sorting hashes")
                memory_store.sort(key=lambda x: x[0])
                end_time = time.time()

                print(
                    f"finished sorting hashes ({end_time - start_time:.2f} sec ~ {num_hashes / (end_time - start_time) / (1024 * 1024):.1f} MB/s)")

                result, num_lookups = self.pom_lookup(memory_store, last_block_hash, last_difficulty)
            else:
                print("Unsupported proof type.")
                sys.exit(1)

            if result == -1:
                print("Proof prefix not found. Validation failed.")
            else:
                print(f"Nonce found: {result}. Validation successful.")
                transaction = get_transaction()
                print(transaction)
                print(last_block_hash)

                if transaction:
                    # Validate transaction here
                    print("Validating transaction...")
                    # Example usage
                    last_hash = last_block_hash
                    transaction_data = transaction

                    add_block_to_server(last_hash, transaction_data,result)

                    # Confirm block
                    confirm_block()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
            return config
        except FileNotFoundError:
            return None

    def check_config_fields(self, config):
        required_fields = ["proof"]
        return all(field in config for field in required_fields)

def print_help():
    print("DSC: DataSys Coin Blockchain v1.0")
    print("Help menu for validator, supported commands:")
    print("./dsc validator help")
    print("./dsc validator pos_check")
    print("./dsc validator")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./dsc-validator.py validator <command>")
        sys.exit(1)

    command = sys.argv[2]

    if command == "help":
        print_help()
    elif command == "validator":
        validator = Validator("dsc-config.yaml")  # Use your actual config file name
        validator.validate()
    elif command == "pos_check":
        print("proof of space is for the next checkpoint")
    else:
        print("Invalid command. Use './dsc-validator.py validator help' for a list of supported commands.")

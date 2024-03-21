import socket
import threading
import jsonpickle
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from block import Block
from transaction import Transaction
from blockchain import Blockchain
from wallet import Wallet

class BlockchainServer:
    def __init__(self, host, port, **kwargs):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.blockchain = kwargs.get('blockchain', None)
        self.wallet = Wallet(self.blockchain, wallet_id=f"User-{port}")
        self.last_metronome_block_hash = ""
        self.executor = ThreadPoolExecutor(max_workers=4)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        print(f"Blockchain server listening on {self.host}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                self.executor.submit(self.handle_client, client_socket, client_address)
        except KeyboardInterrupt:
            print("Server shutting down.")
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        print(f"Accepted connection from {client_address}")

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                decoded_data = data.decode()
                response = self.process_data(decoded_data)

                client_socket.sendall(response.encode())
        except Exception as e:
            print(f"Error handling client: {e}")

        print(f"Connection from {client_address} closed")
        client_socket.close()

    def start_metronome(self):
        interval = 6  # Set the interval to 6 seconds
        while True:
            time.sleep(interval)
            #block = self.blockchain.mine()
            self.last_metronome_block_hash = block.hash
            timestamp = datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
            print(f"{timestamp} New block created, hash {block.hash}, sent to blockchain")

    def process_data(self, data):
        try:
            # Assuming data is a JSON-encoded string
            data_dict = jsonpickle.decode(data)

            if 'action' in data_dict:
                action = data_dict['action']

                if action == 'create_wallet':
                    # Request to create a wallet
                    wallet_id = data_dict.get('wallet_id', '')
                    wallet = Wallet(self.blockchain, wallet_id)

                    # Get or generate keys
                    public_key, private_key = wallet.create()

                    response_data = {
                        'status': 'success',
                        'public_key': public_key,
                        'private_key': private_key,
                    }

                    return jsonpickle.encode(response_data)

                elif action == 'add_block':
                    # Validator is sending a new block



                    block_data = data_dict.get('block_data', None)
                    if block_data:
                        last_hash = block_data.get('last_hash', '')
                        new_block = self.add_block(last_hash, block_data)
                        if new_block:
                            return jsonpickle.encode({'status': 'success', 'message': 'Block added successfully'})
                        else:
                            return jsonpickle.encode({'status': 'error', 'message': 'Failed to add block'})


                elif action == 'metronome':
                    # Extract the hash from the data
                    hash_value = data_dict.get('hash', '')
                    timestamp = data_dict.get('timestamp', '')
                    print(f"Received hash from metronome at {timestamp}: {hash_value}")
                    self.last_metronome_block_hash = data_dict.get('hash', '')
                    # You can perform any required processing with the received hash here

                    return jsonpickle.encode({'status': 'success', 'message': 'Hash received'})

                elif action == 'validator_request':
                    # Validator request for the last block hash from the metronome
                    if data_dict.get('request') == 'GET_LAST_METRONOME_BLOCK_HASH':
                        return jsonpickle.encode({'status': 'success', 'last_metronome_block_hash': self.last_metronome_block_hash})

                else:
                    return jsonpickle.encode({'status': 'error', 'message': 'Invalid action'})

            else:
                return jsonpickle.encode({'status': 'error', 'message': 'No action specified'})

        except Exception as e:
            return jsonpickle.encode({'status': 'error', 'message': str(e)})

    def add_block(self, last_hash, block_data):
        # Perform necessary validations and checks
        # Example: Check if the last_hash matches the hash of the last block in the current blockchain

        # Add the block to the blockchain
        proof = block_data.get('proof', 0)
        new_block = self.blockchain.create_block(proof, last_hash)

        # Print the updated blockchain
        print("Updated Blockchain:")
        for block in self.blockchain.chain:
            print(block)

        return new_block
if __name__ == "__main__":
    blockchain = Blockchain()

    # Print the blockchain
    for block in blockchain.chain:
        print(block)

    server = BlockchainServer(host="localhost", port=8000, blockchain=blockchain)
    server.start()

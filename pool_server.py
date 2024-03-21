import socket
import json
from threading import Thread
from collections import deque


class PoolServer:
    def __init__(self, host='localhost', port=9000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f'Starting pool server on {self.host}:{self.port}...')
        self.client_threads = []

        # Using deque for O(1) insertion and removal at both ends
        self.submitted_transactions = deque()
        self.unconfirmed_transactions = {}

    def _send_response(self, client_socket, message):
        response = json.dumps(message)
        client_socket.sendall(response.encode('utf-8'))

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                decoded_data = data.decode('utf-8')
                request = json.loads(decoded_data)

                if 'transaction_id' in request and 'transaction_data' in request:
                    transaction_id = request['transaction_id']
                    transaction_data = request['transaction_data']

                    # Process the transaction (add to queues, etc.)
                    print(f"Transaction received: {transaction_id}")

                    # Store the transaction in the submitted_transactions queue
                    self.submitted_transactions.append((transaction_id, transaction_data))

                    # Store the transaction in the unconfirmed_transactions dictionary
                    self.unconfirmed_transactions[transaction_id] = transaction_data

                    self._send_response(client_socket, {'message': 'Transaction received successfully'})

                elif 'validator_request' in request:
                    # Handle validator request
                    transaction = self.request_transaction()
                    if transaction:
                        self._send_response(client_socket, transaction)
                    else:
                        self._send_response(client_socket, {'error': 'No transactions available'})
                elif 'confirm_block' in request:
                    # Handle block confirmation
                    self.confirm_block()
                    self._send_response(client_socket, {'message': 'Block confirmed'})
                else:
                    self._send_response(client_socket, {'error': 'Invalid request'})

        finally:
            client_socket.close()

    def request_transaction(self):
        # Implement your logic to serve validator requests here
        # Return the transaction or None if no transactions available
        if self.submitted_transactions:
            transaction_id, transaction_data = self.submitted_transactions.popleft()
            del self.unconfirmed_transactions[transaction_id]
            return {'transaction_id': transaction_id, 'transaction_data': transaction_data}
        else:
            return None

    def confirm_block(self):
        # Clear all transactions from the unconfirmed pile (block confirmed)
        self.unconfirmed_transactions.clear()

    def run(self):
        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"Accepted connection from {address}")
                client_thread = Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
                self.client_threads.append(client_thread)
        except KeyboardInterrupt:
            pass
        finally:
            self.server_socket.close()
            for thread in self.client_threads:
                thread.join()
            print('Pool server stopped.')


if __name__ == '__main__':
    pool_server = PoolServer()
    pool_server.run()

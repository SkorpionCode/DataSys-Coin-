import socket
import threading
import uuid
import requests
import json


client_dbs = {}
client_balances = {}
client_dbs_lock = threading.Lock()

host = "localhost"
port = 5005

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen(10)

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

def send_message(client_socket, message):
    client_socket.send(message.encode())

def handle_client(client, address):
    public_key = client.recv(1024).decode()  # Receive the public key from the client

    with client_dbs_lock:
        client_dbs[public_key] = client
        client_balances[public_key] = 100

    send_message(client, f"Connected with Public Key: {public_key}, Balance: {client_balances[public_key]}")

    print(f"Client {public_key} connected, address: {address}, Balance: {client_balances[public_key]}")

    while True:
        data = client.recv(1024)
        if not data:
            break

        msg = data.decode()

        if msg.startswith("send"):
            parts = msg.split()
            sender_key = public_key  # Use the public key as the sender key
            receiver_key = parts[1]
            amt = int(parts[2])

            with client_dbs_lock:
                sender_client = client_dbs.get(sender_key)
                receiver_client = client_dbs.get(receiver_key)

                if sender_client and receiver_client:
                    sender_bal = client_balances[sender_key]
                    receiver_bal = client_balances[receiver_key]

                    print(f"Sender Key: {sender_key}, Sender Balance: {sender_bal}")
                    print(f"Receiver Key: {receiver_key}, Receiver Balance: {receiver_bal}")
                    print(f"Transaction Amount: {amt}")

                    if amt > sender_bal:
                        send_message(sender_client, "Insufficient funds.")
                    else:
                        # Generate a unique transaction ID using uuid
                        transaction_id = str(uuid.uuid4())

                        client_balances[sender_key] -= amt
                        client_balances[receiver_key] += amt

                        send_message(sender_client, f"Transaction ID: {transaction_id}, Coins sent {amt}, New Balance: {client_balances[sender_key]}")
                        send_message(receiver_client, f"Transaction ID: {transaction_id}, Received {amt} coins, New Balance: {client_balances[receiver_key]}")

                        # Example usage

                        transaction_data = {
                            'sender_key': sender_key,
                            'receiver_key': receiver_key,
                            'amount': amt,
                            'New Balance_for_receiver_key': client_balances[receiver_key],
                            'New Balance_for_sender_key': client_balances[sender_key]

                        }

                        send_transaction_id(transaction_id, transaction_data)

                        print(f"Transaction ID: {transaction_id}, Sent {amt} coins from {sender_key} to {receiver_key}, New Balance for {sender_key}: {client_balances[sender_key]}, New Balance for {receiver_key}: {client_balances[receiver_key]}")

    with client_dbs_lock:
        del client_dbs[public_key]
        del client_balances[public_key]
        client.close()

def send_coins(sender_key, receiver_key, amt):
    with client_dbs_lock:
        sender_client = client_dbs.get(sender_key)
        receiver_client = client_dbs.get(receiver_key)

        if sender_client and receiver_client:
            sender_bal = client_balances[sender_key]
            receiver_bal = client_balances[receiver_key]

            if amt > sender_bal:
                send_message(sender_client, "Insufficient funds.")
            else:
                # Update balances
                client_balances[sender_key] -= amt
                client_balances[receiver_key] += amt

                # Notify clients about the transaction and updated balances
                send_message(sender_client, f"Transaction ID: {transaction_id}, Sent {amt} coins, New Balance: {client_balances[sender_key]}")
                send_message(receiver_client, f"Transaction ID: {transaction_id}, Received {amt} coins, New Balance: {client_balances[receiver_key]}")

                print(f"Transaction ID: {transaction_id}, Sent {amt} coins from {sender_key} to {receiver_key}, New Balance for {sender_key}: {client_balances[sender_key]}, New Balance for {receiver_key}: {client_balances[receiver_key]}")

while True:
    client, address = server.accept()
    client_handler = threading.Thread(target=handle_client, args=(client, address))
    client_handler.start()

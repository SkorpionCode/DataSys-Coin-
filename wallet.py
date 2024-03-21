from datetime import datetime
import base58
import hashlib
import requests
import random
import uuid
from transaction import Transaction
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.backends import default_backend

class Wallet:
    def __init__(self, blockchain, wallet_id):
        self.blockchain = blockchain
        self.node_id = wallet_id
        self.wallet_id = wallet_id
        self.public_key, self.private_key = None, None  # Initialize keys to None

    def generate_key_pair(self):
        # Generate random strings for public and private keys
        public_key_raw = str(random.getrandbits(256))
        private_key_raw = str(random.getrandbits(256))

        # Encode the keys using base58
        public_key = base58.b58encode(bytes(public_key_raw, 'utf-8')).decode('utf-8')
        private_key = base58.b58encode(bytes(private_key_raw, 'utf-8')).decode('utf-8')

        # Change from Blake2b to SHA-256
        hash_function = hashlib.sha256

        # Hashing the public key
        public_key_hash = hash_function(public_key.encode('utf-8')).hexdigest()
        public_key = base58.b58encode(bytes(public_key_hash, 'utf-8')).decode('utf-8')

        # Hashing the private key
        private_key_hash = hash_function(private_key.encode('utf-8')).hexdigest()
        private_key = base58.b58encode(bytes(private_key_hash, 'utf-8')).decode('utf-8')

        # Return the key pair
        return private_key, public_key

    def create(self):
        # Generate new keys
        self.private_key, self.public_key = self.generate_key_pair()

        public_address = base58.b58encode(hashlib.sha256(self.public_key.encode('utf-8')).digest())

        print(f"{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]} DSC v1.0")
        print(f"{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]} DSC Public Address: {self.public_key}")
        print(f"{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]} DSC Private Address: {self.private_key}")
        print(f"{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]} Public key and private key generated")

        return self.public_key, self.private_key

    def get_balance(self):
        return self.blockchain.get_balance(self.wallet_id)

    def create_and_send_transaction(self, to, amount):
        transaction_id = str(uuid.uuid4())[:16]  # Generate a unique transaction ID

        # Create a new transaction with the generated transaction ID
        transaction = Transaction(
            sender=self.wallet_id,
            to=to,
            amount=amount,
            transaction_id=transaction_id
        )

        # Send the transaction to a pool server (simulated here as a localhost endpoint)
        pool_server_url = "http://localhost:8000/receive_transaction"
        data = {
            'transaction_id': transaction_id,
            'transaction_data': transaction.__dict__
        }

        try:
            response = requests.post(pool_server_url, json=data)
            if response.status_code == 200:
                print(f"Transaction {transaction_id} sent successfully.")
                return transaction_id
            else:
                print(f"Failed to send transaction {transaction_id}. Server response: {response.text}")
                return None
        except Exception as e:
            print(f"Error sending transaction {transaction_id}: {e}")
            return None

    def create_transaction(self, to, amount):
        if amount > self.get_balance():
            raise Exception("not enough balance", amount, self.get_balance())

        # Sign the transaction with the private key
        signature = self.private_key.sign(
            f"{self.wallet_id}{to}{amount}".encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return Transaction(self.wallet_id, to, amount, signature)

    # Add any additional wallet-specific methods or functionality here

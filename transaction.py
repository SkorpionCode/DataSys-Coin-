import jsonpickle
import time

class Transaction:
    def __init__(self, sender_key, receiver_key, amount, transaction_id=None, signature=None):
        self.sender_key = sender_key
        self.receiver_key = receiver_key
        self.amount = amount
        self.timestamp = time.strftime("%m/%d/%Y, %H:%M:%S")
        self.transaction_id = transaction_id
        self.signature = signature

    def __str__(self):
        return jsonpickle.encode({
            'sender_key': self.sender_key,
            'receiver_key': self.receiver_key,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'transaction_id': self.transaction_id,
            'signature': self.signature
        })

    def __repr__(self):
        return str(self)

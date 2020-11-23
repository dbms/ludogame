import requests
import json


class UserPayment(object):

    @staticmethod
    def check_transaction_status(amount):
        return {
            'STATUS': 'TXN_SUCCESS',
            'TXNAMOUNT': str(amount),
        }


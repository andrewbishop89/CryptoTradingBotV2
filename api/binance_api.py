"""

"""

from dataclasses import dataclass

from classes.config import MethodType
from api.general_api import API
from functions.setup.setup import retrieve_keys


@dataclass
class BinanceAPI:
    
    def __init__(self, method_type):
        self._method_type = method_type

        base_url = "https://api.binance.com"
        api_key, api_secret = retrieve_keys(self._method_type)

        self._api = API(api_key, api_secret, base_url)

        general_endpoints = [
            "ping",
            "account",
            "exchangeInfo",
        ]

        for endpoint in general_endpoints:
            setattr(self, endpoint, 
                lambda: self._api.send_signed_request('GET', f'/api/v3/{endpoint}')
            )


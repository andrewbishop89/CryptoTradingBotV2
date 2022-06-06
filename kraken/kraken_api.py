#!/usr/bin/python3
#
# kraken_api.py: contains all functions to interact with the kraken exchange api.
#
# Andrew Bishop
# 2022/05/30
#

# modules imported
import requests
import hashlib
import hmac
from urllib.parse import urlencode

from constants.parameters import *
from helper_functions.setup import *

#----------------------------------functions-----------------------------------

# ALL BINANCE FUNCTIONS
# TODO change to work with kraken api
# def send_signed_request(
#         http_method: str,
#         url_path: str,
#         payload: dict = None) -> dict:
#     """
#     Description:
#         Creates a signed API request for specified parameters.
#     Args:
#         http_method (str): http method used in api call
#         url_path (str): api url path specifying request
#         payload (dict, optional): dictionary of all request attributes 
#         (defaults to None)
#     Raises:
#         ConnectionError: incase of a network connection error
#     Returns:
#         dict: api request response
#     """
#     if (payload == None):
#         payload = {}
#     query_string = urlencode(payload)
#     # replace single quote to double quote
#     query_string = query_string.replace('%27', '%22')
#     if query_string:
#         query_string = "{}&timestamp={}".format(query_string, get_timestamp())
#     else:
#         query_string = 'timestamp={}'.format(get_timestamp())

#     url = BASE_URL + url_path + '?' + query_string + \
#         '&signature=' + hashing(query_string)
#     params = {'url': url, 'params': {}}
#     try:
#         response = dispatch_request(http_method)(**params)
#     except ConnectionError:
#         print(f"{RED}ERROR{WHITE}: Could not establish a connection.")
#         raise ConnectionError
#     return response.json()


# def send_public_request(url_path: str, payload: dict = None) -> dict:
#     """
#     Description:
#         Creates a public API request for specified parameters.
#     Args:
#         url_path (str): api url path specifying request
#         payload (dict, optional): dictionary of all request attributes 
#         (defaults to None)
#     Raises:
#         ConnectionError: incase of a network connection error
#     Returns:
#         dict: api request response
#     """
#     if (payload == None):
#         payload = {}
#     query_string = urlencode(payload, True)
#     url = BASE_URL + url_path

#     if query_string:
#         url = url + '?' + query_string
#     try:
#         response = dispatch_request('GET')(url=url)
#     except ConnectionError:
#         print(f"{RED}ERROR{WHITE}: Could not establish a connection.")
#         raise ConnectionError
#     return response.json()


# def hashing(query_string: str) -> str:
#     """
#     Description:
#         Hashes the string inputted as argument using SHA-256.
#     Args:
#         query_string (str): query string for api request
#     Returns:
#         str: hashed string for api requests
#     """
#     return hmac.new(
#         API_SECRET.encode('utf-8'),
#         query_string.encode('utf-8'),
#         hashlib.sha256).hexdigest()


# def dispatch_request(http_method: str) -> dict:
#     """
#     Description:
#         Dispatches an API request by getting ready to be sent.
#     Args:
#         http_method (str): http method for request
#     Returns:
#         dict: api request status
#     """
#     session = requests.Session()
#     session.headers.update({
#         'Content-Type': 'application/json;charset=utf-8',
#         'X-MBX-APIKEY': API_KEY
#     })
#     return {
#         'GET': session.get,
#         'DELETE': session.delete,
#         'PUT': session.put,
#         'POST': session.post,
#     }.get(http_method, 'GET')

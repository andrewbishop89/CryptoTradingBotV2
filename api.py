#!/usr/bin/python3
#
# api.py: contains all the functions involving the use of the API directly. 
# (note functinos like buy_trade and sell_trade are found in trade.py)
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
from parameters import *
from setup import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM http_method(str): http method used in api call
#PARAM url_path(str): api url path specifiying request
#PARAM payload(dict): dictionary of all request attributes
#RETURN (dict): api request response
def send_signed_request(http_method: str, url_path: str, payload: dict={}):
    query_string = urlencode(payload)
    # replace single quote to double quote
    query_string = query_string.replace('%27', '%22')
    if query_string:
        query_string = "{}&timestamp={}".format(query_string, get_timestamp())
    else:
        query_string = 'timestamp={}'.format(get_timestamp())

    url = BASE_URL + url_path + '?' + query_string + \
        '&signature=' + hashing(query_string)
    params = {'url': url, 'params': {}}
    try:
        response = dispatch_request(http_method)(**params)
    except ConnectionError:
        print(f"{RED}ERROR{WHITE}: Could not establish a connection.")
        raise ConnectionError
    return response.json()

#PARAM url_path(str): api url path specifiying request
#PARAM payload(dict): dictionary of all request attributes
#RETURN (dict): api request response
def send_public_request(url_path, payload={}):
    query_string = urlencode(payload, True)
    url = BASE_URL + url_path
    if query_string:
        url = url + '?' + query_string
    try:
        response = dispatch_request('GET')(url=url)
    except ConnectionError:
        print(f"{RED}ERROR{WHITE}: Could not establish a connection.")
        raise ConnectionError
    return response.json()

#PARAM query_string(str): query string for api request
#RETURN (str): hashed string for api requests
def hashing(query_string: str):
    return hmac.new(
        API_SECRET.encode('utf-8'), 
        query_string.encode('utf-8'),
        hashlib.sha256).hexdigest()

#PARAM http_method(str): http method for request
#RETURN (dict): api request status
def dispatch_request(http_method: str):
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json;charset=utf-8',
        'X-MBX-APIKEY': API_KEY
    })
    return {
        'GET': session.get,
        'DELETE': session.delete,
        'PUT': session.put,
        'POST': session.post,
    }.get(http_method, 'GET')

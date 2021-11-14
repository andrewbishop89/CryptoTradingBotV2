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


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM real(bool): True for real API, False for paper money
#RETURN none
def init_api_keys(real=True):
    global API_KEY, API_SECRET, BASE_URL

    with open('keys.txt', 'r') as f:
        lines = f.readlines()
        #NOTE these are for the binance API
        if real == False:
            API_KEY = lines[0][:-1]
            API_SECRET = lines[1][:-1]
            BASE_URL = "https://testnet.binance.vision"
        elif real == True:
            API_KEY = lines[3][:-1]
            API_SECRET = lines[4][:-1]
            BASE_URL = "https://api.binance.com"


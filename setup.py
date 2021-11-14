#!/usr/bin/python3
#
# setup.py: contains all the functions to setup the program.
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
            

#PARAM interval(int): interval in int form to be converted to str form
#RETURN (int): str value of interval
def encode_interval(interval):
    if type(interval) == str:
        return interval
    if interval/60 < 1:
        return str(interval) + 'm'
    else:
        return str(interval//60) + 'h'

#PARAM interval(str): interval in string form to be converted to nunber of 
# mintues
#RETURN (int): number of minutes the interval is
def decode_interval(interval):
    if type(interval) == int:
        return interval
    if interval[-1] == 'm':
        return int(interval[:-1])
    if interval[-1] == 'h':
        return int(interval[:-1])*60
    if interval[-1] == 'd':
        return int(interval[:-1])*60*24
    print(f"{RED}ERROR{WHITE} The interval {interval} is unrecognizable.")
    raise ValueError

#PARAM ts(float): unix time stamp
#RETURN (float): returns formatted unix time stamp to match with binance 
# time stamps
def convert_time(ts: float):
    if '.' in str(ts):
        ts = int(ts)
    else:
        ts /= 1000
    return ts

#PARAM interval(str): kline interval used
#PARAM limit(int): number of candles before end time
#PARAM end(float): unix time stamp for end time (default is current time)
#RETURN (float): the time stamp of limit interval candles before end
def kline_start_time(interval: str, limit: int, end: float=convert_time(time.time())):
    interval = decode_interval(interval)
    return end-60*interval*limit

#PARAM klines(dict): the dictionary of candles to be converted to DataFrame
#RETURN (DataFrame): the dataframe version of the klines dictionary
def format_binance_klines(klines: dict):
    return pd.DataFrame(
        klines, 
        index='t', 
        columns=['o', 'h', 'l', 'c', 'v', 'n']).astype(float)

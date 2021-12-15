#!/usr/bin/python3
#
# setup.py: contains all the functions to setup the program.
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
import datetime
import time
import os
import pandas as pd

from parameters import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            
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

#PARAM klines(dict): the list of candles to be converted to DataFrame
#RETURN (DataFrame): the dataframe version of the klines list
def klines_dict_to_df(klines):
    return pd.DataFrame(klines, columns=['o','c','h','l','t','n','v']).set_index('t')

#RETURN (int): formatted current unix timestamp
def get_timestamp():
    return int(time.time()*1000)

#
#
def format_binance_klines(klines):
    formatted_klines = []
    for kline in klines:
        formatted_klines.append({})
        formatted_klines[-1]['t'] = float(kline[0])
        formatted_klines[-1]['o'] = float(kline[1])
        formatted_klines[-1]['h'] = float(kline[2])
        formatted_klines[-1]['l'] = float(kline[3])
        formatted_klines[-1]['c'] = float(kline[4])
        formatted_klines[-1]['v'] = float(kline[5])
        formatted_klines[-1]['n'] = float(kline[8])
    return klines_dict_to_df(formatted_klines)


def get_time(ts):
    return datetime.utcfromtimestamp(ts).strftime('%H:%M')


#PARAM symbol(str):
#PARAM interval(str):
def init_coin(symbol: str, interval: str):
    file_path = os.path.join(
        "data", "live_data",
        f"{interval}",
        f"{symbol.upper()}_{interval}.csv")
    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            f.write("")
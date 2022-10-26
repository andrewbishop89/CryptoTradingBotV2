#!/usr/bin/python3
#
# setup.py: contains all the functions to setup the program.
#
# Andrew Bishop
# 2021/11/13
#

from datetime import datetime
import time
import sys
import os
import pandas as pd
from pprint import pprint, pformat
import csv
import threading
from typing import Tuple, Dict, List
from enum import Enum

from classes.config import TradeType

            
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
def kline_start_time(
    interval: str, 
    limit: int, 
    end: float=convert_time(time.time())):
    
    interval = decode_interval(interval)
    return end-60*interval*limit

#PARAM klines(dict): the list of candles to be converted to DataFrame
#RETURN (DataFrame): the dataframe version of the klines list
def klines_dict_to_df(klines):
    return pd.DataFrame(
        klines, 
        columns=['o','c','h','l','t','n','v']).set_index('t')

#RETURN (int): formatted current unix timestamp
def get_timestamp():
    return int(time.time()*1000)

#PARAM klines: candles to be formated from dictionary to DataFrame
#RETURN (DataFrame): DataFrame of formatted candles
def format_binance_klines(klines):
    formatted_klines = []
    for kline in klines:
        formatted_klines.append({})
        formatted_klines[-1]['t'] = int(kline[0]/1000)
        formatted_klines[-1]['o'] = float(kline[1])
        formatted_klines[-1]['h'] = float(kline[2])
        formatted_klines[-1]['l'] = float(kline[3])
        formatted_klines[-1]['c'] = float(kline[4])
        formatted_klines[-1]['v'] = float(kline[5])
        formatted_klines[-1]['n'] = float(kline[8])
    return klines_dict_to_df(formatted_klines)

#PARAM string(str): string to be padded with whitespace
#PARAM padding(float=0.3): percentage of terminal width to use for padding
#PARAM terminal_width(float=os.get_terminal_size().columns): terminal window 
# character width
#RETURN (string): string with padding formatted by terminal width
def format_string_padding(
    string: str,
    padding: float=0.25,
    terminal_width: float=None):
    if (terminal_width == None):
        terminal_width = 1 if (len(sys.argv) > 1) else \
            os.get_terminal_size().columns
    return string.ljust(int(terminal_width*padding))


#PARAM ts: unix time stamp to be converted to hour/minute format
#RETURN (string): string formatted in hour/minute format
def get_time(ts):
    return datetime.utcfromtimestamp(ts).strftime('%H:%M')


#PARAM symbol(str):
#PARAM interval(str):
#RETURN (none)
def init_coin(symbol: str, interval: str):
    file_path = os.path.join("data", "live_data", f"{interval}", f"{symbol.upper()}_{interval}.csv")
    if not os.path.isfile(file_path):
        with open(file_path, 'w') as f:
            f.write("")

#PARAM file_path(str): file to be written to
#PARAM data(list): list of data of row
#RETURN (none)
def add_row_to_csv(file_path: str, data: list):
    with open(file_path, "a") as csv_file:
        csv_obj = csv.writer(csv_file)
        csv_obj.writerow(data)

#PARAM initial(float): initial price of trade
#PARAM final(float): final price of trade
#PARAM paper(bool): paper money flag, true if paper money trade
#RETURN (float): profit percentage * 100 to decimal places
def get_profit(initial: float, final: float, paper: bool=False):
    if paper:
        #rough estimate of fee
        return round((final/initial-1)*100, 2) - 0.02
    
        #real fee
        #paper_initial = (initial * 0.999)
        #return round((((final / paper_initial) * 0.999) - 1) * 100, 2)
    else:
        return round((final/initial-1)*100,2)

#PARAM sleep_time(int=300): amount of seconds to sleep
#PARAM terminal_width(int=os.get_terminal_size().columns): width of terminal 
# window
#RETURN (none)
def lost_connection_sleep(
        sleep_time: int = 300,
        terminal_width: int = None):
    if (terminal_width == None):
        terminal_width = 1 if (len(sys.argv) > 1) else \
            os.get_terminal_size().columns

    print_string = f"{RED}ERROR {WHITE} ReadTimeout Error Raised in Thread" + \
        f" {threading.current_thread().name}. Sleeping: {sleep_time}"
    print(print_string.ljust(terminal_width), end='\r')

    for index in range(1, sleep_time+1):
        print_string = f"{RED}ERROR {WHITE} ReadTimeout Error Raised in " + \
            f"Thread {threading.current_thread().name}. Sleeping: " + \
            f"{sleep_time-index}"
        print(print_string.ljust(terminal_width), end='\r')
        time.sleep(1)

    print_string = f"{RED}ERROR {WHITE} ReadTimeout Error Raised in Thread" + \
        f" {threading.current_thread().name}. Slept for " + \
        f"{round(sleep_time/60)} minutes\n"
    print(print_string.ljust(terminal_width), end='\r')

    return


def retrieve_keys(trade_type: TradeType) -> Tuple[str, str]:
    """
    Retrieves specified API keys from environment.

    :param trade_type TradeType: specifies which API keys to return
    :return Tuple[str, str]: a tuple of the public and secret api keys
    """
    if trade_type == TradeType.REAL:
        keys = (os.environ["BINANCE_REAL_K"], os.environ["BINANCE_REAL_S"])
    else:
        keys = (os.environ["BINANCE_PAPER_K"], os.environ["BINANCE_PAPER_S"])
    return keys  


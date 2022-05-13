#!/usr/bin/python3
#
# method_2_data.py: contains functions for method 2 data collection for crypto 
# bot version 2.
#
# Andrew Bishop
# 2022/03/10
#
#

# modules imported
import sys
import threading
import pync
import time
import os
from multiprocessing import Pool
from pprint import pprint

from data_collection import *
from market import *
from trade import *
from analysis import *
from parameters import *
from method_2_backtest import *
from method_2_func import *

def data_2(symbol: str, trade_flag: bool, low_w: int, mid_w: int, high_w: int):

    # download 1h klines
    while True and (not trade_flag):
        try:
            long_klines = download_recent_klines(
                symbol=symbol,
                interval="1h",
                limit=high_w).reset_index()
        except requests.exceptions.ConnectionError:
            print(f"{RED}ERROR {WHITE}Could Not Download 1h {symbol}.")
            time.sleep(15)
        else:
            if len(long_klines) < high_w:
                print(f"{GREY}ERROR {WHITE} Ending {symbol}-Thread." + \
                    f" Klines: {len(long_klines)}, Need: {high_w}")
                sys.exit()
            break

    # download 5m klines
    while True:
        try:
            short_klines = download_recent_klines(
                symbol=symbol,
                interval="5m",
                limit=high_w).reset_index()
        except requests.exceptions.ConnectionError:
            print(f"{RED}ERROR {WHITE}Could Not Download 5m {symbol}.")
            time.sleep(15)
        else:
            break

    # calculate long EMA values
    long_EMAs = pd.DataFrame([
        EMA(long_klines['c'], low_w),
        EMA(long_klines['c'], mid_w),
        EMA(long_klines['c'], high_w)
        ], index = [low_w, mid_w, high_w])

    # calculate short EMA values
    short_EMAs = pd.DataFrame([
        EMA(short_klines['c'], low_w),
        EMA(short_klines['c'], mid_w),
        EMA(short_klines['c'], high_w)
        ], index = [low_w, mid_w, high_w])
    
    return short_klines, short_EMAs, long_EMAs
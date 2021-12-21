#!/usr/bin/python3
#
# data_collection.py: contains all functions to download data
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
from binance.client import Client
import os

from parameters import *
from setup import *


#----------------------------------functions-----------------------------------

#PARAM: symbol(str) - string of current symbol to download
#PARAM: interval(str) - interval of klines to return
#PARAM: limit(int) - number of klines to download
#PARAM: start_time(int) - start time in form of unix timestamp
#RETURN: (DataFrame) - requested candles
def historical_klines(
        symbol: str,
        interval: str,
        limit: int,
        start_time: int = -1):

    try:
        interval = decode_interval(interval)
        client = Client(API_KEY, API_SECRET)
        if start_time == -1:
            start_time = kline_start_time(interval, limit)
        if limit > 1000:
            remainder = limit % 1000
            if remainder:
                klines = client.get_historical_klines(
                    symbol=symbol,
                    interval=encode_interval(interval),
                    limit=remainder,
                    start_str=str(start_time)
                )[:remainder]
                start_time += remainder*60*interval
            else:
                klines = []
            factors = int((limit-remainder)/1000)
            for index in range(factors):
                klines += client.get_historical_klines(
                    symbol=symbol,
                    interval=encode_interval(interval),
                    limit=1000,
                    start_str=str(start_time)
                )[:1000]
                start_time += 1000*60*interval
        else:
            klines = client.get_historical_klines(
                symbol=symbol,
                interval=encode_interval(interval),
                limit=limit,
                start_str=str(start_time)
            )[:limit]
        return format_binance_klines(klines)
    except:
        if not len(klines):
            print(f"{RED}ERROR{WHITE} No klines were downloaded.")
            raise ValueError
        return format_binance_klines(klines)

#PARAM
#RETURN
def download_to_csv(symbol: str, interval: str, limit: int=500):
    klines = download_recent_klines(symbol, interval, limit)
    klines_to_csv(klines, symbol, interval)
    return klines

#PARAM klines(DataFrame/dict): candles to be sent to csv
#PARAM symbol(str): symbol of candles
#PARAM interval(str): interval of candles
#RETURN none
def klines_to_csv(klines, symbol: str, interval: str):
    if (type(klines) != pd.DataFrame):
        klines = klines_dict_to_df(klines)
    init_coin(symbol, interval)
    klines.to_csv(os.path.join("data", "live_data", f"{interval}",
        f"{symbol.upper()}_{interval}.csv"))
    
#PARAM (): TODO
#RETURN (): TODO
def download_recent_klines(symbol, interval, limit=500):
    """Returns list of last 'limit' klines maxing at 1000. Use historical klines for other 1000 limit."""
    client = Client(API_KEY, API_SECRET)
    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    return format_binance_klines(klines)

# NOTE extra args are for backtesting.
def get_klines(symbol, limit, interval='1m', offset=-1, backtest_index=False, all_klines=False):

    klines = []
    count = 0
    while True:
        try:
            klines = pd.read_csv(os.path.join(
                "data", 
                "live_data",
                f"{interval}", 
                f"{symbol.upper()}_{interval}.csv"))
            
            if len(klines):
                break
            else:
                download_to_csv(symbol, interval)
        except:
            pass
        count += 1
        color = SECONDARY_COLOR if count < 3 else RED
        #print(f"{color}ERROR{WHITE} Could not get klines for {interval} {symbol}.")
        time.sleep(2)
    if offset == -1:
        return klines.iloc[-int(limit):]
    elif offset != -1:
        return klines.iloc[-int(limit)-int(offset):-int(offset)]
    raise ValueError

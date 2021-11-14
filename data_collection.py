#!/usr/bin/python3
#
# data_collection.py: contains all functions to download data
#
# Andrew Bishop, Ryan Manak
# 2021/11/13
#

# modules imported
from parameters import *
from setup import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

#PARAM: symbol(str) - string of curreny symbol to download
#PARAM: interval(str) - interval of klines to return
#PARAM: limit(int) - number of klines to download
#PARAM: start_time(int) - start time in form of unix timestamp
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
        return klines_dict_to_df(klines)
    except:
        if not len(klines):
            print(f"{RED}ERROR{WHITE} No klines were downloaded.")
            raise ValueError
        return klines_dict_to_df(klines)

#PARAM klines(DataFrame/dict): candles to be sent to csv
#PARAM symbol(str): symbol of candles
#PARAM interval(str): interval of candles
#RETURN none
def klines_to_csv(klines, symbol: str, interval: str):
    if (type(klines) != pd.DataFrame):
        klines = klines_dict_to_df(klines)
    klines.to_csv("SOLUSDT_1h.csv")
    

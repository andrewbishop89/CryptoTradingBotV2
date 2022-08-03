#!/usr/bin/python3
#
# data_collection.py: contains all functions to download data
#
# Andrew Bishop
# 2021/11/13
#

# modules imported
from binance.client import Client
import binance
import os
import requests
import logging
from random import randint

from constants.parameters import API_KEY, API_SECRET
from setup.setup import *

# ----------------------------------functions-----------------------------------


def historical_klines(symbol: str, interval: str, limit: int, start_time: int = None) -> pd.DataFrame:
    """
    Description:
        Downloads historical klines (candles) for specified arguments.
    Args:
        symbol (str): string of current symbol to download
        interval (str): interval of klines to return
        limit (int): number of klines to download
        start_time (int, optional): start time in form of unix timestamp 
        (defaults to None)
    Raises:
        ValueError: incase no candles were downloaded
    Returns:
        pd.DataFrame: requested candles in chronological order (-1 item is 
        most recent)
    """
    try:
        interval = decode_interval(interval)
        client = Client(API_KEY, API_SECRET)
        if start_time:
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


def candle_data_file_path(symbol: str, interval: str,
                          historical: bool = False) -> str:
    """
    Description:
        Returns the file path for the corresponding input parameters.
    Args:
        symbol (str): symbol of coin data
        interval (str): interval of coin data
        historical (bool, optional): true if historical data, else false
            (defaults to False)
    Returns:
        str: file path for input data
    """
    if historical:
        return os.path.join('data', 'historical_data', str(interval),
                            f"{symbol}_{interval}.csv")
    else:
        return os.path.join('data', 'live_data', str(interval),
                            f"{symbol}_{interval}.csv")


def download_for_backtest(symbol: str, interval: str, limit: int = 1000):
    klines = historical_klines(symbol, interval, limit)
    klines_to_csv(klines, symbol, interval, historical=True)
    return klines


def download_to_csv(symbol: str, interval: str,
                    limit: int = 500) -> pd.DataFrame:
    """
    Description:
        Downloads specified candles and saves them to a csv file.
    Args:
        symbol (str): symbol of currency to download
        interval (str): interval of candles to download
        limit (int, optional): amount of candles to download (defaults to 500)
    Returns:
        pd.DataFrame: the downloaded candles that were save to the file
    """
    klines = download_recent_klines(symbol, interval, limit)
    klines_to_csv(klines, symbol, interval)
    return klines


def klines_to_csv(klines: pd.DataFrame, symbol: str, interval: str,
                  historical: bool = False):
    """
    Description:
        Saves the candles passed as argument to a csv file.
    Args:
        klines (pd.DataFrame): candles to be saved to csv
        symbol (str): symbol of candles
        interval (str): interval of candles
    Returns:
        None
    """
    if (type(klines) != pd.DataFrame):
        klines = klines_dict_to_df(klines)
    init_coin(symbol, interval)
    klines.to_csv(candle_data_file_path(symbol, interval, historical))


def get_saved_klines(symbol: str, interval: str, limit: int = None,
                     historical: bool = False) -> pd.DataFrame:
    """
    Description:
        Returns locally saved klines for specified parameters.
    Args:
        symbol (str): symbol of klines
        interval (str): interval of klines
        limit (int, optional): amount of candles to return (defaults to 1000)
        historical (bool, optional): True if historical data, false otherwise 
            (defaults to False)
    Returns:
        pd.DataFrame: klines specified by parameters
    """
    klines = pd.read_csv(candle_data_file_path(symbol, interval, historical))
    if (limit == None):
        return klines
    else:
        return klines.iloc[:limit]


def download_recent_klines(symbol: str, interval: str,
                           limit: int = 500) -> pd.DataFrame:
    """
    Description:
        Returns the last X most recent candles where X is the limit 
        parameter.
    Args:
        symbol (str): symbol of candles to download
        interval (str): interval of candles to download
        limit (int, optional): amount of candles to download (defaults to 500)
    Returns:
        pd.DataFrame: the candles that were downloaded
    """
    while True:
        try:
            if (limit > 1000):  # this func cant do over 1000 func but other func can
                return historical_klines(symbol, interval, limit)
            client = Client(API_KEY, API_SECRET)
            klines = client.get_klines(
                symbol=symbol, interval=interval, limit=limit)
        except binance.exceptions.BinanceAPIException:
            # use random to stagger incase multiple api errors are raised simultaneously
            wait_time = randint(30, 90)
            logger.warning(
                f"Binance API Error. Retrying in {wait_time}s.", exc_info=True)
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError:
            logger.warning(
                f"Connection Error. Retrying in 20s.", exc_info=True)
            time.sleep(20)
        else:
            break
    return format_historical_klines(klines)


def get_klines(symbol: str, limit: int, interval: str = '1m',
               offset: int = -1) -> pd.DataFrame:
    """
    Description:
        Returns candles specified by parameters.
    Args:
        symbol (str): symbol of candles to return
        limit (int): amount of candles to return
        interval (str, optional): interval of candles to return (defaults to 
        '1m')
        offset (int, optional): offset from time of execution for candles 
        (start time) (defaults to -1)
    Raises:
        ValueError: incase no candles could be found
    Returns:
        pd.DataFrame: candles specified by input parameters
    """
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
        time.sleep(2)
    if offset == -1:
        return klines.iloc[-int(limit):]
    elif offset != -1:
        return klines.iloc[-int(limit)-int(offset):-int(offset)]
    raise ValueError


def delete_old_data():
    """
    Description:
        Deletes all the (only) live data to reduce storage.
    """
    fp = os.path.join("data", "live_data")
    interval_dirs = os.listdir(fp)
    for interval_dir in interval_dirs:
        dir_fp = os.path.join(fp, interval_dir)
        if os.path.isdir(dir_fp):
            data_files = os.listdir(dir_fp)
            for data_file in data_files:
                os.remove(os.path.join(dir_fp, data_file))
    logger.debug("Deleted old live data.")
    return

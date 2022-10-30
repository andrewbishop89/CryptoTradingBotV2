#!/usr/bin/python3
#
# websocket.py: contains all functions for the websocket connection.
#
# Andrew Bishop
# 2021/11/25
#

# modules imported
import json
import websockets
import sys
import os
import socket
import urllib3
import asyncio
import logging
import threading

from functions.setup.setup import *
from functions.data_collection.data_collection import *


# ----------------------------------functions-----------------------------------

# TODO add check so that websocket disconnects and reconnects after 24h


def format_kline(kline: dict) -> pd.DataFrame:
    """
    Description:
        Converts kline from dict to dataframe.
    Args:
        kline (dict): dictionary of kline to be formatted
    Return:
        (pd.DataFrame): formatted kline dataframe
    """
    return pd.DataFrame(data={
        't': [int(kline['t']/1000)],
        'o': [float(kline['o'])],
        'c': [float(kline['c'])],
        'h': [float(kline['h'])],
        'l': [float(kline['l'])],
        'n': [float(kline['n'])],
        'v': [float(kline['v'])],
    }).set_index("t")


def init_websocket_klines(symbol: str, interval: str, file_lock: threading.Lock, limit: int = 500) -> None:
    """
    Description:
        Initiates all the kline data necessary before connecting to the socket stream. Specifically downloads the last 500 candles
    Args:
        symbol (str): symbol of klines
        interval (str): interval of klines
        file_lock (threading.Lock): threading lock to avoid thread collisions when data from file is accessed
        limit (int): Defaults to 500. number of klines to download in file
    """
    init_coin(symbol, interval)
    data_path = os.path.join(
        "data", "live_data", f"{interval}", f"{symbol.upper()}_{interval}.csv")
    file_lock.acquire()
    download_recent_klines(symbol, interval, limit).to_csv(data_path)
    file_lock.release()
    asyncio.run(connect_async_websocket(symbol, interval, file_lock))


async def connect_async_websocket(symbol: str, interval: str, file_lock: threading.Lock):
    """
    Description:
        Connects asynchronous main loop for data collection.
    Args:
        symbol (str): symbol of klines
        interval (str): interval of klines
        file_lock (threading.Lock): threading lock to avoid thread collisions when data from file is accessed
        limit (int): Defaults to 500. number of klines to download in file
    """
    data_path = os.path.join(
        "data", "live_data", f"{interval}", f"{symbol.upper()}_{interval}.csv")
    ws_path = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
    async with websockets.connect(ws_path) as ws:
        while True:
            try:
                current_kline = format_kline(json.loads(await ws.recv())['k'])

                file_lock.acquire()
                klines = pd.read_csv(data_path).set_index(
                    "t")  # load existing klines
                file_lock.release()

                if klines.index[-1] != current_kline.index[-1]:  # if new candle has opened
                    klines = klines.iloc[1:, :]  # remove first candle
                else:  # update existing candle
                    klines = klines.iloc[:-1, :]  # remove last candle
                # update with newest candle
                klines = klines.append(current_kline)

                file_lock.acquire()
                klines.to_csv(data_path)
                file_lock.release()

                # reset stream after 24h
                time_now = datetime.utcfromtimestamp(
                    time.time()-7*3600).strftime('%H:%M')
                if time_now == "11:29":
                    logger.info(
                        f"Daily Ending of {threading.current_thread().name}: {symbol}.{interval}")
                    return  # end function loop if it is time for daily reset
            except (requests.exceptions.ConnectionError, urllib3.exceptions.NewConnectionError):
                logger.warning(
                    "Could not connect to network. Waiting for 30s.", exc_info=True)
                time.sleep(30)
            except socket.gaierror as e:
                logger.warning(
                    "Websocket error has been raised. Waiting for 20s.", exc_info=True)
                time.sleep(20)


def connect_websocket(symbol: str, interval: str, file_lock: threading.Lock, limit: int = 500) -> threading.Thread:
    """
    Description:
        Creates a new thread for the websocket and creates connection.
    Args:
        symbol (str): symbol of klines
        interval (str): interval of klines
        file_lock (threading.Lock): threading lock to avoid thread collisions when data from file is accessed
        limit (int): Defaults to 500. number of klines to download in file
    Return:
        (threading.Thread): thread that is used for websocket connection
    """
    websocket_thread = threading.Thread(target=init_websocket_klines, args=[
                                        symbol, interval, file_lock, limit], daemon=True)
    websocket_thread.start()
    websocket_thread.name = f"{symbol}/{interval}_Websocket_Thread"
    return websocket_thread


def update_klines(symbol: str, interval: str, file_lock: threading.Lock) -> pd.DataFrame:
    """
    Description:
        Reads csv file for klines in thread safe manner.
    Args:
        symbol (str): symbol of kline data
        interval (str): interval of kline data
        file_lock (threading.Lock): thread safe lock of data file
    Returns:
        pd.DataFrame: dataframe with most recent updated klines
    """
    data_path = os.path.join(
        "data", "live_data", interval, f"{symbol.upper()}_{interval}.csv")
    file_lock.acquire()
    while True:
        try:
            klines = pd.read_csv(data_path)
            break
        except OSError:
            logger.debug(
                f"{symbol} {interval} - Retrying in 20s.", exc_info=True)
            time.sleep(20)
    file_lock.release()
    return klines
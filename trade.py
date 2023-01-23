#!/usr/bin/python3
#
# trade.py 
#
# Andrew Bishop
# 2022/10/11
#

import os
import time


from backtest import backtest

from classes import config
from classes.trade import TradeType
from classes.config import MethodType


# from functions.analysis import analysis
from functions.data_collection import data_collection, market, websocket_func
from functions.setup import setup
from functions.trade import trade

from rich.pretty import pprint
from rich import print

import binance


if __name__ == "__main__":
    
    setup.set_method_type(MethodType.PAPER)    

    symbol = "BTCUSDT"
    limit = 200
    interval = "1m"
    print(symbol, limit, interval)
    print()

   
    keys = setup.retrieve_keys()



    # ASYNC SOCKET
    # async_client = binance.client.AsyncClient(*keys)
    # print(async_client)
    # socket_manager = binance.streams.BinanceSocketManager(async_client)
    # print(socket_manager)
    # ws = socket_manager.kline_socket(symbol, interval)
    # print(ws)

    # THREAD SOCKET
    thread_socket = binance.streams.ThreadedWebsocketManager(*keys)
    print(thread_socket)
    
    import json, pandas as pd

    def callback(ws, msg):
        pd.DataFrame(json.loads(msg)).to_csv("test.csv")

    thread = thread_socket.start_kline_socket(callback, symbol, interval)
    time.sleep(100)


    # klines_obj = websocket_func.LiveKlines(symbol, interval, limit) 
    # pprint(klines_obj.update_klines())
    # time.sleep(3)
    # pprint(klines_obj.update_klines())
    print("Done")


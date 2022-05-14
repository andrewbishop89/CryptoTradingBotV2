#!/usr/bin/python3
#
# websocket.py: contains all functions for the websocket connection.
#
# Andrew Bishop
# 2021/11/25
#

# modules imported
import json
import websocket
import sys
import os
import threading

from constants.parameters import *
from helper_functions.setup import *
from helper_functions.data_collection import *


#----------------------------------functions-----------------------------------

# TODO add check so that websocket disconnects and reconnects after 24h

def format_kline(kline):
    return pd.DataFrame(data={
        't': [float(kline['t'])],
        'o': [float(kline['o'])],
        'c': [float(kline['c'])],
        'h': [float(kline['h'])],
        'l': [float(kline['l'])],
        'n': [float(kline['n'])],
        'v': [float(kline['v'])],
    }).set_index("t")

def connect_websocket(symbol, interval):
    socket = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@kline_{interval}"
    
    init_coin(symbol, interval)
    
    data_path = os.path.join("data", "live_data", f"{interval}", f"{symbol.upper()}_{interval}.csv")
    
    download_recent_klines(symbol, interval).to_csv(data_path)
    
    ws = websocket.WebSocketApp(socket, on_message=on_message)
    print(f"Connecting {interval} {symbol} Websocket.")
    
    ws.run_forever()

def on_message(ws, message):
    json_message = json.loads(message)
    current_kline = format_kline(json_message['k'])
    symbol = json_message['s']    
    interval = json_message['k']['i']

    data_path = os.path.join("data", "live_data", f"{interval}", f"{symbol.upper()}_{interval}.csv")

    klines = pd.read_csv(data_path).set_index("t") # load existing klines
    
    if klines.index[-1] != current_kline.index[-1]: # if new candle has opened
        klines = klines.iloc[1:, :] # remove first candle
    else: # update existing candle
        klines = klines.iloc[:-1, :] # remove last candle 
        
    klines = klines.append(current_kline) # update with newest candle
    klines.to_csv(data_path)
    
    return 

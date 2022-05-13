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

from constants.parameters import *
from helper_functions.setup import *
from helper_functions.data_collection import *


#----------------------------------functions-----------------------------------

def format_kline(kline):
    return pd.Series(data=[
        float(kline['c']),
        float(kline['o']),
        float(kline['h']),
        float(kline['l']), ],
    index=[kline['t']])

def connect_websocket(symbol, interval, lock):
    
    
    socket = f"wss://stream.binance.com:9443/ws/{symbol.lower()}\
        @kline_{interval}"
    init_coin(symbol, interval)
    data_path = os.path.join("data", "live_data", f"{interval}", 
        f"{symbol.upper()}_{interval}.csv")
    print("Downloading Candles.")
    download_recent_klines(symbol, interval).to_csv(data_path)
    ws = websocket.WebSocketApp(socket, on_message=on_message)
    print("Connecting Websocket.")
    ws.run_forever()

def on_message(ws, message):
    print("STARTED FUNCTION")
    try:
        if get_time(convert_time(time.time())) == "23:59":
            raise TimeoutError
        json_message = json.loads(message)
        current_kline = format_kline(json_message['k'])
        symbol = json_message['s']
        interval = current_kline['i']
        data_path = os.path.join("data", "live_data", 
            f"{interval}", f"{symbol.upper()}_{interval}.csv")

        print("THREAD: Acquiring")
        lock.acquire()
        print("THREAD: Acquired")
        with open(data_path, 'r') as klines_file:
            klines = json.load(klines_file)
        print("THREAD: Releasing")
        lock.release()
        print("THREAD: Released")
        try:
            if current_kline['x'] == True:
                print("THREAD: Acquiring")
                lock.acquire()
                print("THREAD: Acquired")
                with open(data_path, 'w') as csv_file:
                    new_klines = download_recent_klines(symbol, interval)
                    while not len(new_klines):
                        new_klines = download_recent_klines(symbol, interval)
                        time.sleep(5)
                    json.dump(new_klines, csv_file, indent=2)
                print("THREAD: Releasing")
                lock.release()
                print("THREAD: Released")
                return
            else:
                klines.pop(-1)
                klines.append(current_kline)
                if current_kline['T'] < (convert_time(time.time())-60*decode_interval(interval)):
                    print(
                        f"{RED}ERROR{WHITE} Connection Error in thread: {interval} {symbol}")
                    sys.exit()
        except KeyError:
            try:
                klines.pop(-1)
            except IndexError:
                pass
            klines.append(current_kline)

        print("THREAD: Acquiring")
        lock.acquire()
        print("THREAD: Acquired")
        with open(data_path, 'w') as json_file:
            json.dump(klines, json_file, indent=2)
        print("THREAD: Releasing")
        lock.release()
        print("THREAD: Released")
        
        time.sleep(0.1)

    except (KeyboardInterrupt, TimeoutError) as ex:
        print("THREAD: Acquiring")
        lock.acquire()
        print("THREAD: Acquired")
        with open(data_path, 'w') as json_file:
            json.dump(klines, json_file, indent=2)
        print("THREAD: Releasing")
        lock.release()
        print("THREAD: Released")
        print(f"{PRIMARY_COLOR}{ex.__name__} has been raised.\n{WHITE}")
        sys.exit()
    return
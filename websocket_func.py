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

from parameters import *
from setup import *
from data_collection import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


def connect_websocket(symbol, interval):
    socket = f"wss://stream.binance.com:9443/ws/{symbol.lower()}\
        @kline_{interval}"
    init_coin(symbol, interval)
    data_path = os.path.join("data", "live_data", f"{interval}", 
        f"{symbol.upper()}_{interval}.csv")
    with open(data_path, 'w') as json_file:
        download_recent_klines(symbol, interval).to_csv(data_path)
    ws = websocket.WebSocketApp(socket, on_message=on_message)
    ws.run_forever()


def on_message(ws, message):
    try:
        if get_time(convert_time(time.time())) == "23:59":
            raise TimeoutError
        json_message = json.loads(message)
        current_kline = json_message['k']
        pd.Series(data=[
            float(current_kline['c']),
            float(current_kline['o']),
            float(current_kline['h']),
            float(current_kline['l']), ],
            index=[current_kline['t']])
        symbol = json_message['s']
        interval = current_kline['i']
        data_path = os.path.join("data", "live_data", 
            f"{interval}", f"{symbol.upper()}_{interval}.csv")

        with open(data_path, 'r') as klines_file:
            klines = json.load(klines_file)
        try:
            if current_kline['x'] == True:
                with open(data_path, 'w') as csv_file:
                    new_klines = download_recent_klines(symbol, interval)
                    while not len(new_klines):
                        new_klines = download_recent_klines(symbol, interval)
                        time.sleep(5)
                    json.dump(new_klines, csv_file, indent=2)
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

        with open(data_path, 'w') as json_file:
            json.dump(klines, json_file, indent=2)
        #with open(data_backup_path, 'w') as json_file:
        #    json.dump(klines, json_file, indent=2)
        time.sleep(0.5)

    except KeyboardInterrupt:
        with open(data_path, 'w') as json_file:
            json.dump(klines, json_file, indent=2)
        #with open(data_backup_path, 'w') as json_file:
        #    json.dump(klines, json_file, indent=2)
        print(f"{PRIMARY_COLOR}Keyboard Interrupt.\n{WHITE}")
        sys.exit()
    except TimeoutError:
        with open(data_path, 'w') as json_file:
            json.dump(klines, json_file, indent=2)
        #with open(data_backup_path, 'w') as json_file:
        #    json.dump(klines, json_file, indent=2)
        print(f"{PRIMARY_COLOR}Time Out Error has been raised.\n{WHITE}")
        raise TimeoutError
    return

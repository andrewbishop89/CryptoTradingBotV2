#!/usr/bin/python3
#
# method_1.py: contains functions for method 1 of crypto bot version 2.
#
# Andrew Bishop, Ryan Manak
# 2021/11/25
#

# modules imported
import os
import pync
import threading

from data_collection import *
from graphing import graph
from market import *
from trade import *
from parameters import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def trade_loop(
    lock: threading.Lock, 
    symbol: str, 
    interval: str, 
    paper_flag: bool):
    
    if (not paper_flag):
        buy_id, sell_quantity = buy_trade(symbol, 15) #buy in
    
    stop_loss = 0.1
    
    buy_price = current_price_f(symbol)

    max_price = buy_price
    stop_price = buy_price*(1-stop_loss)
    
    while True:
        klines = download_to_csv(symbol, interval)
        current_price = klines.iloc[-1]['c']
        current_high = klines.iloc[-1]['h']
        
        max_price = max(max_price, current_high)
        
        if (current_price < stop_price): # if below stop loss take losses
            if (not paper_flag):
                sell_trade(symbol, quantity=sell_quantity)
            sell_price = current_price_f(symbol)
            profit = round((sell_price/buy_price-1)*100, 2)
            profit_color = GREEN if profit > 0 else RED
            print(f"{profit_color}PROFIT{WHITE}: {profit}%\n\n")
            break
        
        #top value - 'stop_loss' percent of buy in price
        stop_price = max_price - buy_price*stop_loss
        time.sleep(30)
        
    lock.acquire()
    current_trades.remove(symbol)
    lock.release()
        
    return

def main():
    #Parameters
    gain_threshold_value = 10 #gain required in 5min period for buy in
    interval = '1m'
    paper_flag = True #if true than using paper money, else using real money
    
    lock = threading.Lock() #for thread synchronization
    global current_trades #list of all coins currently being traded
    current_trades = []
    
    # MAIN LOOP
    while True:
        try: #try-except incase api requests raise error or loss of connection
        
            #Find coins to trade
            top_coins = top_gainers(gain_threshold_value)
            max_gain = 1
            
            lock.acquire()
            for coin in current_trades: #if coin already being traded, skip it
                if coin in top_coins:
                    top_coins.remove(coin)
            lock.release()
            
            for coin in top_coins.index:
                init_coin(coin, interval) #if new coin, create file for data
                klines = download_to_csv(coin, interval) #download recent data
                
                last_klines = klines.tail(5) #only analyze last 5 candles
                for index in range(1,5):
                    try:
                        if (last_klines.iloc[-index]['c'] < \
                            last_klines.iloc[-index]['o']):
                            continue
                    except IndexError: #incase coin has less than 5 candles
                        break
                    else:
                        gain = last_klines.iloc[-1]['c']/ \
                            last_klines.iloc[-index]['o']
                        max_gain = max(gain, max_gain)
                        if (gain > (1+gain_threshold_value/100)):
                            #notify computer about buying in
                            pync.notify(f"{coin}: {round(gain*100-100,2)}%", 
                                title="CTB2")
                            print(f"{GREY}CRITERIA ACHIEVED{WHITE} buying \
                                into {coin}.")
                            lock.acquire()
                            current_trades.append(coin)
                            lock.release()
                            #creating trade loop thread for coin
                            threading.Thread(
                                target = trade_loop, 
                                args = [lock, 
                                        coin, 
                                        interval,
                                        paper_flag]
                                ).start()
                            time.sleep(2)
            
            print(f"Number of Coins: {len(top_coins)}\t\t  \
                {normalize_time(time.time())}\t\t  Last Max Gain: \
                {round(max_gain*100-100,2)}%  \t\t  Thread Count: \
                {threading.active_count()}  ", end='\r')
                        
            time.sleep(60*1.5)
            
        except requests.exceptions.ReadTimeout:
            print(f"{RED}ERROR {WHITE} ReadTimeout Error Raised. Sleeping \
                for 5 minutes.")
            time.sleep(60*5)

main()

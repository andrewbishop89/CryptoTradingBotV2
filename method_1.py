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

from data_collection import *
from graphing import graph
from market import *
from trade import *
from parameters import *


# functions
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

def trade_loop(symbol: str, interval: str):
    
    buy_id, sell_quantity = buy_trade(symbol, 40) #buy in
    
    price_fluctuation = 0.1
    
    buy_price = current_price_f(symbol)

    max_price = buy_price
    stop_price = buy_price*(1-price_fluctuation)
    
    while True:
        klines = download_to_csv(symbol, interval)
        current_price = klines.iloc[-1]['c']
        current_high = klines.iloc[-1]['h']
        
        max_price = max(max_price, current_high)
        
        if (current_price < stop_price): # if below stop loss take losses
            sell_trade(symbol, quantity=sell_quantity)
            sell_price = current_price_f(symbol)
            print(f"PROFIT: {round((1-sell_price/buy_price)*100, 2)}%")
            break
        
        if (max_price > ((1+price_fluctuation/2)*buy_price)):
            price_fluctuation = max_price - buy_price*price_fluctuation #top value - 10% buy in
        
        time.sleep(45)
        
    return

def main():
    gain_threshold_value = 10 #gain required in 5min period for buy in
    interval = '1m'
    
    # MAIN LOOP
    while True:
        
        #Find coins to trade
        top_coins = top_gainers(gain_threshold_value)
        print(f"Number of Coins: {len(top_coins)}")
        for coin in top_coins.index:
            init_coin(coin, interval)
            klines = download_to_csv(coin, interval)
            
            last_klines = klines.tail(5)
            for index in range(1,5):
                try:
                    if (last_klines.iloc[-index]['c'] < last_klines.iloc[-index]['o']):
                        continue
                except IndexError: #incase coin has less than 5 candles
                    break
                else:
                    gain = last_klines.iloc[-1]['c']/last_klines.iloc[-index]['o']
                    if (gain > (1+gain_threshold_value/100)):
                        pync.notify(f"{coin}: {round(gain*100-100,2)}%", 
                            title="CTB2")
                        trade_loop(coin, interval)
            
        time.sleep(60*1.5)


main()

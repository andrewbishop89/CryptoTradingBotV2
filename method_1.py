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

def main():
    gain_threshold_value = 10 #gain required in 5min period for buy in
    larger_interval = '5m'
    
    # MAIN LOOP
    while True:
        
        #Find coins to trade
        top_coins = top_gainers(gain_threshold_value)
        print(f"Number of Coins: {len(top_coins)}")
        for coin in top_coins.index:
            init_coin(coin, larger_interval)
            klines = download_to_csv(coin, larger_interval)
            
            kline = klines.iloc[-1]
            if (kline['c']/kline['o'] > (1+gain_threshold_value/100)):
                pync.notify(f"{coin}: {round(kline['c']/kline['o']*100-100,2)}%", title="CTB2")
                print(coin, kline)

        time.sleep(60*5)

main()

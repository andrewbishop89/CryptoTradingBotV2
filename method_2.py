#!/usr/bin/python3
#
# method_2.py: contains functions for method 2 of crypto bot version 2.
#
# Andrew Bishop
# 2022/02/28
#
# Crontab: 
# @reboot sleep 120 && cd ~/CryptoTradingBotV2 && /Library/Frameworks/
# Python.framework/Versions/3.8/bin/python3 ~/CryptoTradingBotV2/method_1.py 
# >> ~/CryptoTradingBotV2/cron_logs.txt 2>&1
#

# modules imported
from concurrent.futures import thread
import sys
import threading
import pync
import time
import os
from multiprocessing import Pool
from pprint import pprint

from data_collection import *
from market import *
from trade import *
from analysis import *
from parameters import *
from backtest_2 import *


#------------------------------------TODOs-------------------------------------

#TODO: 

#----------------------------------functions-----------------------------------

def run_all(symbols):
    
    print(f"Live Symbols ({len(symbols)}):")
    threading.current_thread.name = "MAIN-Thread"
    threads_list = []
    
    global trade_flag, current_balance
    # flag indicating active trade (thread safe, linked with trade_lock)
    trade_flag = False 
    # current balance (thread safe, linked with balance_lock)
    current_balance = 15 
    
    for symbol in symbols:
        threads_list += [threading.Thread(target=live_method_2, args=[symbol])]
        threads_list[-1].name = f"{symbol}-Thread"
        threads_list[-1].start()
        print(f"\tStarting {threads_list[-1].name}.")
    print()
        
    thread_count = len(threads_list)+1
    while True:
        current_count = threading.active_count()
        if current_count != thread_count:
            for t in threads_list:
                if not t.is_alive():
                    print(f"{RED}ERROR {WHITE}{t.name} Is Not Responding. Thread Count: {current_count}")
                    threads_list.remove(t)
                    break
                    
        time.sleep(2*60)

def live_method_2(symbol, print_flag=False):#trade_lock, balance_lock):

    # EMA windows
    low_w = 8
    mid_w = 13
    high_w = 21
    
    # trade flag
    trade_flag = False
    
    init_flag = True
    
    # start backtest loop
    try:
        while True:
            
            # sleep
            # ================================================================
                    
            if not init_flag:        
                start = time.time()
                #trade_lock.acquire()
                sleep_time = 2.5*60 if (not trade_flag) else 30
                #trade_lock.release()
                end = time.time()
                time.sleep(sleep_time - (end-start))
            else:
                init_flag = False
                
            # download klines and calculate EMAs
            # ================================================================
            
            # download 1h klines
            long_klines = download_recent_klines(
                symbol=symbol,
                interval="1h",
                limit=high_w).reset_index()

            # download 5m klines
            short_klines = download_recent_klines(
                symbol=symbol,
                interval="5m",
                limit=high_w).reset_index()
            
            # calculate long EMA values
            long_EMAs = pd.DataFrame([
                EMA(long_klines['c'], low_w),
                EMA(long_klines['c'], mid_w),
                EMA(long_klines['c'], high_w)
                ], index = [low_w, mid_w, high_w])
            
            # calculate short EMA values
            short_EMAs = pd.DataFrame([
                EMA(short_klines['c'], low_w),
                EMA(short_klines['c'], mid_w),
                EMA(short_klines['c'], high_w)
                ], index = [low_w, mid_w, high_w])
            
            # check for trade criteria met
            # ================================================================
            
            current_kline = short_klines.iloc[-1] # current candle
            current_price = current_kline['c'] # current price
            
            #trade_lock.acquire()
            if not trade_flag: # only check buy in criteria if looking for buy in
                #trade_lock.release()
                
                # 1: 1h -> 8 EMA > 21 EMA)
                criteria_1 = (long_EMAs.loc[8, high_w-1] > long_EMAs.loc[21, high_w-1])
                if not criteria_1:
                    continue
                
                # 2: 5m -> 8 EMA > 13 EMA > 21 EMA
                criteria_2 = (short_EMAs.loc[8, high_w-1] > short_EMAs.loc[13, high_w-1]) and \
                    (short_EMAs.loc[13, high_w-1] > short_EMAs.loc[21, high_w-1])
                if not criteria_2:
                    continue
                
                # 3: 5m -> price > 8 EMA (last kline)
                criteria_3 = (current_kline['h'] > short_EMAs.loc[8, high_w-2])
                if not criteria_3:
                    continue
                
                # 4: 5m -> price < 8 EMA (current kline)
                criteria_4 = (current_kline['l'] < short_EMAs.loc[8, high_w-1])
                if not criteria_4:
                    continue
                
                # 5: buy in
                trade_flag = True
                buy_price = current_price
                buy_time = short_klines.loc[high_w-1, 't']
                print(f"Bought into {symbol} @{buy_time} for {buy_price}.")
                
                # 6: stop loss at min(last 5 lows)
                stop_price = min(short_klines.loc[high_w-5:high_w-1,'l'])
                percent_profit = buy_price/stop_price-1
                
                # 7: 50% take profit at 1:1, 50% take profit at 1:2 (reset 
                # stop loss to buy in if 1:1 reached)
                profit_price_1 = buy_price*(1+percent_profit)
                profit_price_2 = buy_price*(1+2*percent_profit)
                
                profit_flag = False
                
            #else:
                #trade_lock.release()
                
            # buy into trade
            # ================================================================
                
            #trade_lock.acquire()
            if trade_flag:
                #trade_lock.release()
                
                # STOP LOSS
                if (current_price < stop_price): # if stop loss is reached
                    profit = (-percent_profit) if not profit_flag else 0
                    #total_profit += profit
                    #print(RED, profit, WHITE, total_profit)
                    print(f"LOSS:\t\t\t{RED}{round(profit*100,2)}%{WHITE}") if print_flag else None
                    #trade_lock.acquire()
                    trade_flag = False
                    #trade_lock.release()
                    profit_flag = False
                    continue

                # FIRST TAKE PROFIT
                if not profit_flag: # if first profit not reached yet
                    if (current_price > profit_price_1):
                        profit = (percent_profit/2)
                        #total_profit += profit
                        #print(BLUE, profit, WHITE, total_profit)
                        print(f"Profit 1:\t\t{GREEN}{round(profit*100,2)}%{WHITE}") if print_flag else None
                        profit_flag = True
                        stop_price = buy_price
                        
                # SECOND TAKE PROFIT
                if profit_flag: # if first profit already reached
                    if (current_price > profit_price_2):
                        profit = percent_profit
                        #total_profit += profit
                        #print(GREEN, profit, WHITE, total_profit)
                        print(f"Profit 2:\t\t{GREEN}{round(profit*100,2)}%{WHITE}") if print_flag else None
                        trade_flag = False
                        profit_flag = False
                        continue
            #else:
                #trade_lock.release()
                
            # ================================================================
    except Exception as e:
        print(f"{RED}ERROR{WHITE} In {threading.current_thread.name}")
        raise e
    

#------------------------------------main--------------------------------------



if __name__ == '__main__':
    
    symbols = [
        "XRPUSDT",
        "FILUSDT",
        "TRXUSDT",
        "ETHUSDT",
        "BTCUSDT",
        "BNBUSDT",
        "LTCUSDT",
        "ADAUSDT",
        "XLMUSDT",
        "SOLUSDT",
        "DOTUSDT",
        "VETUSDT",
        #"DOGEUSDT",
        #"SHIBUSDT",
        #"CAKEUSDT",
    ] + top_gainers(5).index.tolist()
    
    symbols = list(dict.fromkeys(symbols)) # remove duplicates
    
    
    #backtest_all(symbols)
    run_all(symbols)
    
    



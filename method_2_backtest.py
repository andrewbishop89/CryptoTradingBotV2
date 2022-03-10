#!/usr/bin/python3
#
# method_2_backtest.py: contains functions for backtest method 2 of crypto bot 
# version 2.
#
# Andrew Bishop
# 2022/03/1
#
# Crontab: 
# @reboot sleep 120 && cd ~/CryptoTradingBotV2 && /Library/Frameworks/
# Python.framework/Versions/3.8/bin/python3 ~/CryptoTradingBotV2/method_1.py 
# >> ~/CryptoTradingBotV2/cron_logs.txt 2>&1
#

# modules imported
import sys
import threading
from typing import List
import pync
import os
from multiprocessing import Pool
from pprint import pprint

from data_collection import *
from market import *
from trade import *
from analysis import *
from parameters import *


#------------------------------------TODOs-------------------------------------

#TODO: 

#----------------------------------functions-----------------------------------

def backtest_all(symbols: List):
    """
    Description:
        Backtests all symbols listed for method 2.
    Args:
        symbols (List): all symbols to be backtested.
    """
    print("Backtest Symbols:")
    for s in symbols:
        print(f"\t{s}")
    print("\n\nStarting Backtest.")
    with Pool(10) as p:
        net_profit = sum(p.map(backtest_method_2, symbols))
    print(f"\nNet Profit: ".rjust(25) + f"{GREEN if (net_profit > 0) else RED}{round(net_profit*100,2)}%{WHITE}\n")


def backtest_method_2(
        symbol: str, 
        days: int=10, 
        new: bool=True, 
        print_flag: bool=False) -> float:
    """
    Description:
        Run backtest method 2 for symbol.
    Args:
        symbol (str): symbol of coin.
        days (int, optional): number of days to backtest for (defaults to 10)
        new (bool, optional): True if download new candles (defaults to True)
        print_flag (bool, optional): True if prints are to be displayed
        (defaults to False)
    Returns:
        float: total profit during backtest calculations.
    """

    # current symbol    
    total_profit = 1

    # EMA windows
    low_w = 8
    mid_w = 13
    high_w = 21
    
    # backtest limit
    limit = 288*days
    
    # download 1h klines
    long_klines = download_for_backtest(
        symbol = symbol,
        interval = "1h",
        limit = int(limit/12)+1).reset_index() \
            if new else get_saved_klines(
                symbol, 
                "1h", 
                limit=int(limit/12)+1, 
                historical=True).reset_index()

    # download 5m klines
    short_klines = download_for_backtest(
        symbol = symbol,
        interval = "5m",
        limit = limit).reset_index() \
            if new else get_saved_klines(
                symbol,
                "5m",
                limit=limit,
                historical=True).reset_index()

    # if coin has no data
    if (len(short_klines) < 10) or (len(long_klines) == 0):
        return 0
    
    # 1h index
    long_i = short_klines.loc[0,'t'] - short_klines.loc[0,'t']%3600_000 
    base_long_i = long_klines.loc[0, 't'] - 3600_000
    long_klines = long_klines.set_index('t')
    
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
    
    buy_flag = False # init to no open trade
    
    # start backtest loop
    try:
        for short_i in range(len(short_klines)):
            
            # current price
            current_kline = short_klines.loc[short_i]
            
            # increment long index if necessary
            long_i = float(short_klines.loc[short_i, 't'] - short_klines.loc[short_i, 't']%3600_000)
            long_ema_i = (long_i - base_long_i) / 3600_000
            
            if not buy_flag: # only check buy in criteria if looking for buy in
            
                # 1: 1h -> 8 EMA > 21 EMA
                criteria_1 = (long_EMAs.loc[8, long_ema_i] > long_EMAs.loc[21, long_ema_i])
                if not criteria_1:
                    continue
                
                # 2: 5m -> 8 EMA > 13 EMA > 21 EMA
                criteria_2 = (short_EMAs.loc[8, short_i] > short_EMAs.loc[13, short_i]) and \
                    (short_EMAs.loc[13, short_i] > short_EMAs.loc[21, short_i])
                if not criteria_2:
                    continue
                
                # 3: 5m -> price > 8 EMA (last kline)
                criteria_3 = (current_kline['h'] > short_EMAs.loc[8, short_i-1])
                if not criteria_3:
                    continue
                
                # 4: 5m -> price < 8 EMA (current kline)
                criteria_4 = (current_kline['l'] < short_EMAs.loc[8, short_i])
                if not criteria_4:
                    continue
            
                # 5: 5m -> current candle closes
                # wait for candle to close
                
                # 6: buy in
                buy_flag = True
                buy_price = short_klines.loc[short_i, 'c']
                buy_time = short_klines.loc[short_i, 't']
                
                # 7: stop loss at min(last 5 lows)
                stop_price = min(short_klines.loc[short_i-5:short_i,'l'])
                percent_profit = buy_price/stop_price-1
                
                # 8: 50% take profit at 1:1, 50% take profit at 1:2 (reset 
                # stop loss to buy in if 1:1 reached)
                profit_price_1 = buy_price*(1+percent_profit)
                profit_price_2 = buy_price*(1+2*percent_profit)
                
                profit_flag = False
                
                
            if buy_flag:
                
                current_price = current_kline['c'] # current price
                
                # STOP LOSS
                if (current_price < stop_price): # if stop loss is reached
                    profit = (1-percent_profit) if not profit_flag else 1
                    total_profit *= profit
                    #print(RED, profit, WHITE, total_profit)
                    print(f"LOSS:\t\t\t{RED}{round(profit*100,2)}%{WHITE}") if print_flag else None
                    buy_flag = False
                    profit_flag = False
                    continue

                # FIRST TAKE PROFIT
                if not profit_flag: # if first profit not reached yet
                    if (current_price > profit_price_1):
                        profit = (percent_profit/2+1)
                        total_profit *= profit
                        #print(BLUE, profit, WHITE, total_profit)
                        print(f"Profit 1:\t\t{GREEN}{round(profit*100,2)}%{WHITE}") if print_flag else None
                        profit_flag = True
                        stop_price = buy_price
                        
                # SECOND TAKE PROFIT
                if profit_flag: # if first profit already reached
                    if (current_price > profit_price_2):
                        profit = 1 + percent_profit
                        total_profit *= profit
                        #print(GREEN, profit, WHITE, total_profit)
                        print(f"Profit 2:\t\t{GREEN}{round(percent_profit*100,2)}%{WHITE}") if print_flag else None
                        buy_flag = False
                        profit_flag = False
                        continue
                        
                        
    except (IndexError, KeyError):
        pass    
    
    total_profit -= 1
    print(f"{symbol} Profit: ".rjust(25) + f"{GREEN if (total_profit > 0) else RED}{round((total_profit)*100,2)}%{WHITE}")
    return total_profit
    

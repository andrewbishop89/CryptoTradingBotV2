#!/usr/bin/python3
#
# method_2.py: contains functions for method 2 of crypto bot version 2.
#
# Andrew Bishop
# 2022/02/28
#
# Crontab: 
# @reboot sleep 60 && cd ~/CryptoTradingBotV2 && /Library/Frameworks/Python.framework/Versions/3.8/bin/python3 ~/CryptoTradingBotV2/method_2.py >> ~/CryptoTradingBotV2/cron_logs.txt 2>&1
#

# modules imported
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
from method_2_func import *


#------------------------------------TODOs-------------------------------------

# TODO: add trades.csv and run similar to profits.csv so that if the program 
# crashes you can still see if there was an existing trade and then continue 
# with it

# TODO: add async websocket connection

# TODO: change threading lock to dictionary full of all threading locks

# TODO: add check to see if there are any new coins in top gainers that can 
# have new threads created for them

# TODO: add stop loss check to see if it is outside one standard deviation of 
# the last hour, if so, make that the stop loss

# TODO: add dynamic stop loss that changes to maximum - stop loss percent and 
# changes as price changes

#----------------------------------functions-----------------------------------

def run_all(symbols, p_f=False):
    
    print(f"Starting Live Symbols ({len(symbols)}) at " + \
          f"{normalize_time(time.time()-8*3600)}")
    threading.current_thread.name = "MAIN-Thread"
    threads_list = []
    
    # dictionary of all locks
    locks = {
        "trade": threading.Lock(),
        "profit_file": threading.Lock()
    }
    
    for symbol in symbols:
        if symbol[-4:] != "USDT":
            print(f"\tSkipping {symbol}.") if p_f else None
            continue
        threads_list += [threading.Thread(target=live_method_2, \
            args=[symbol, locks, p_f])]
        threads_list[-1].name = f"{symbol}-Thread"
        threads_list[-1].start()
        print(f"\tStarting {threads_list[-1].name}.")  if p_f else None
        time.sleep(60*5/len(symbols) if len(symbols) > 125 else 0)
    print()
        
    thread_count = len(threads_list)+1
    while True:
        current_count = threading.active_count()
        if current_count != thread_count:
            for t in threads_list:
                if not t.is_alive():
                    print(f"{RED}ERROR {WHITE}{t.name} Is Not Responding." + \
                        f" Thread Count: {current_count}")
                    threads_list.remove(t)
                    break
                    
        time.sleep(2*60)



def live_method_2(symbol, locks, print_flag=False):

    # real money flag
    real_money = False

    # EMA windows
    low_w = 8
    mid_w = 13
    high_w = 21
    
    # risk multiplier
    risk_multiplier = 2
    
    # profit split ratio
    profit_split_ratio = 0
    
    # minimum profit for trade
    min_profit = 0.15
    
    # flags
    trade_flag = False
    init_flag = True
    
    # start backtest loop
    try:
        while True:
            
            # sleep
            # ================================================================
                    
            if (not init_flag):
                start = time.time()
                #trade_lock.acquire()
                sleep_time = 60*2.5 if (not trade_flag) else 60*0.5
                #trade_lock.release()
                end = time.time()
                time.sleep(sleep_time - (end-start))
            else:
                init_flag = False
                
            # download klines and calculate EMAs
            # ================================================================
            
            # download 1h klines
            while True and (not trade_flag):
                try:
                    long_klines = download_recent_klines(
                        symbol=symbol,
                        interval="1h",
                        limit=high_w).reset_index()
                except requests.exceptions.ConnectionError:
                    print(f"{RED}ERROR {WHITE}Could Not Download 1h {symbol}.")
                    time.sleep(15)
                else:
                    break

            # download 5m klines
            while True:
                try:
                    short_klines = download_recent_klines(
                        symbol=symbol,
                        interval="5m",
                        limit=high_w).reset_index()
                except requests.exceptions.ConnectionError:
                    print(f"{RED}ERROR {WHITE}Could Not Download 5m {symbol}.")
                    time.sleep(15)
                else:
                    break
            
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
            # only check buy in criteria if looking for buy in
            if not trade_flag:
                #trade_lock.release()
                
                # 1: 1h -> 8 EMA > 21 EMA)
                criteria_1 = (long_EMAs.loc[8, high_w-1] > \
                    long_EMAs.loc[21, high_w-1])
                if not criteria_1:
                    continue
                
                # 2: 5m -> 8 EMA > 13 EMA > 21 EMA
                criteria_2 = (short_EMAs.loc[8, high_w-1] > \
                    short_EMAs.loc[13, high_w-1]) and \
                    (short_EMAs.loc[13, high_w-1] > \
                    short_EMAs.loc[21, high_w-1])
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
                
                # 5: 5m -> low > 21 EMA (current kline)
                criteria_5 = (current_kline['l'] > short_EMAs.loc[21, high_w-1])
                if not criteria_5:
                    continue
                
                # 6: buy in
                # difference of 1h EMA over buy price
                buy_price = float(current_price_f(symbol)) if real_money else current_price
                stop_price = min(short_klines.loc[high_w-5:high_w-1,'l'])
                percent_profit = buy_price/stop_price-1
                trade_flag = (percent_profit*100 > min_profit)
                if not trade_flag:
                    continue
                
                difference_1h = (long_EMAs.loc[low_w, high_w-1] - \
                    long_EMAs.loc[high_w, high_w-1])/buy_price*100
                
                if real_money:
                    #if (difference_1h < 0.9):
                    #    trade_flag = False
                    #    continue
                    balance = account_balance("USDT")
                    if (balance < 10):
                        trade_flag = False
                        #print(f"{RED}ERROR {WHITE} {symbol}, Balance: {balance}, Need: 10")
                        time.sleep(60*1.5)
                        continue
                    buy_id, profit_quantity = \
                        buy_trade(symbol=symbol, quote_quantity=balance)
                    buy_time = time.time()
                    print(f"\tBUY ID: {buy_id}") if print_flag else None
                else:
                    buy_time = short_klines.loc[high_w-1, 't']
                
                # 7: stop loss at min(last 5 lows)
                
                
                # 8: 50% take profit at 1:1, 50% take profit at 1:2 (reset 
                # stop loss to buy in if 1:1 reached)
                profit_price = buy_price*(1+percent_profit*risk_multiplier)
                # index for which take profits have been reached
                profit_index = 1 
                
                # 9: record buy in values
                # short closing values
                short_closing = short_klines.loc[:, 'c']
                # standard deviation of last 15 short values
                std_5m = short_closing[high_w-15:high_w-1].std()
                
                ticker = daily_ticker_24hr(symbol)
                # 24h volume
                volume_24h = float(ticker['volume'])
                volume_rel = round(short_klines.loc[:, 'v'].iloc[-6:].sum()*48/volume_24h*100,2)
                # 24h price change percent
                price_24h = float(ticker['priceChangePercent'])
                
                print(f"\tIN: {symbol}".ljust(20) + \
                      f"@{int(buy_time)} for".ljust(15) + \
                      f"{round(buy_price,4)} ".rjust(20) + \
                      f"{round(stop_price,4)}".rjust(20) + \
                      f"{round(profit_price,4)} ".rjust(20) + \
                      f"{round(percent_profit*100,2)}%".rjust(20)) if \
                          print_flag else None
                continue
                
            #else:
                #trade_lock.release()
                
            # buy into trade
            # ================================================================
                
            #trade_lock.acquire()
            if trade_flag:
                #trade_lock.release()
                
                profit_split_ratio = 1
                
                # STOP LOSS
                if (current_price < stop_price): # if stop loss is reached
                    profit = (-percent_profit) if (profit_index < 2) else 0
                    trade_flag = False
                    
                    if real_money:
                        sell_id = sell_trade(
                            symbol=symbol, 
                            quantity=profit_quantity)[0]
                        print(f"\tSELL ID: {sell_id}") if print_flag else None
                    
                    display_loss(symbol, profit_index, profit)
                    
                    if (profit_index < 2):
                        log_profits(
                            "{:.4f}".format(profit*100), 
                            symbol, 
                            buy_price, 
                            current_price, 
                            buy_time, 
                            time.time(), 
                            f"S", 
                            profit_split_ratio, 
                            std_5m, 
                            difference_1h,
                            price_24h,
                            volume_24h,
                            volume_rel,
                            risk_multiplier,
                            locks["profit_file"], 
                            real=real_money)
                    continue

                # TAKE PROFIT
                if (current_price > profit_price):
                    # divide by profit index because quantity decays by factor 
                    # of 2 each time
                    profit = (current_price / buy_price) - 1
                    profit *= ((1-profit_index) / profit_index)
                    if True:
                        profit = ((current_price/buy_price)-1)/profit_index
                        trade_flag = False

                    if real_money:
                        profit_quantity *= (1 - profit_split_ratio)
                        sell_id = sell_trade(
                            symbol=symbol, 
                            quantity=profit_quantity)[0]
                        print(f"\tSELL ID: {sell_id}")
                        
                    display_profit(symbol, profit_index, profit)
                    
                    log_profits(
                        "{:.4f}".format(profit*100), 
                        symbol, 
                        buy_price, 
                        current_price, 
                        buy_time, 
                        time.time(), 
                        f"P_{profit_index}", 
                        profit_split_ratio, 
                        std_5m, 
                        difference_1h, 
                        price_24h,
                        volume_24h,
                        volume_rel,
                        risk_multiplier,
                        locks["profit_file"], 
                        real=real_money)
                    
                    # new stop is og buy price
                    stop_price = buy_price 
                    # new buy is og profit price
                    buy_price = profit_price 
                    # new profit is new buy + percent profit
                    profit_price = buy_price*(1+percent_profit) 
                    # increment profit index
                    profit_index += 1
                    
            #else:
                #trade_lock.release()
                
            # ================================================================
    except Exception as e:
        print(f"{RED}ERROR{WHITE} In {symbol}-Thread.")
        raise e
    

#------------------------------------main--------------------------------------

def main():
    #backtest_all(symbols)
    
    symbols = top_volume_gainers(200).index
    run_all(symbols, False)

if __name__ == '__main__':
    main()